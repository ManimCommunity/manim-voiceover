import importlib
import sched
import time
import wave
from pathlib import Path
from typing import Callable, Dict, List, Mapping, Optional, Protocol, Tuple, cast

import pyaudio
from pydub import AudioSegment
from pydub.playback import play

from manim_voiceover.helper import trim_silence, wav2mp3

HOST_API_INDEX = 0


class RecorderStream(Protocol):
    def is_active(self) -> bool: ...

    def stop_stream(self) -> None: ...

    def close(self) -> None: ...


class KeyboardListener(Protocol):
    def start(self) -> None: ...


RECORDING_START_MESSAGES = ("Press and hold the 'r' (or Shift^R if on Wayland) key to begin recording",)
FIRST_RECORDING_MESSAGES = (
    "Wait for 1 second, then start speaking.",
    "Wait for at least 1 second after you finish speaking.",
    "This is to eliminate any sounds that may come from your keyboard.",
    "The silence at the beginning and end will be trimmed automatically.",
    "You can adjust this setting using the `trim_silence_threshold` argument.",
    "These instructions are only shown once.",
)
RECORDING_END_MESSAGES = ("Release the 'r' (or Shift^R if on Wayland) key to end recording",)


def _create_keyboard_listener(
    on_press: Callable[[object], bool],
    on_release: Callable[[object], bool],
) -> KeyboardListener:
    try:
        keyboard_module = importlib.import_module("pynput.keyboard")
    except ImportError as exc:
        raise ImportError(
            'Missing or unusable pynput keyboard backend. Run `pip install "manim-voiceover[recorder]"` '
            "and make sure a supported display backend is available."
        ) from exc

    listener_factory = getattr(keyboard_module, "Listener")
    if not callable(listener_factory):
        raise RuntimeError("pynput.keyboard.Listener is not callable.")

    # pragma: no mutate start
    return cast(
        Callable[[Callable[[object], bool], Callable[[object], bool]], KeyboardListener],
        listener_factory,
    )(on_press, on_release)
    # pragma: no mutate end


class MyListener:
    def __init__(self) -> None:
        self.key_pressed = False
        self._keyboard_listener: Optional[KeyboardListener] = None

    def start(self) -> None:
        self._keyboard_listener = _create_keyboard_listener(self.on_press, self.on_release)
        self._keyboard_listener.start()

    def on_press(self, key: object) -> bool:
        if hasattr(key, "r") or hasattr(key, "shift_r"):
            self.key_pressed = True
        else:
            char = getattr(key, "char", None)
            if char == "r" or char == "shift_r":
                self.key_pressed = True

        return True

    def on_release(self, key: object) -> bool:
        if hasattr(key, "r") or hasattr(key, "shift_r"):
            self.key_pressed = False
        else:
            char = getattr(key, "char", None)
            if char == "r" or char == "shift_r":
                self.key_pressed = False

        return True


class Recorder:
    def __init__(
        self,
        format: int = pyaudio.paInt16,
        channels: Optional[int] = None,
        rate: int = 44100,
        chunk: int = 512,
        device_index: Optional[int] = None,
        trim_silence_threshold: float = -40.0,
        trim_buffer_start: int = 200,
        trim_buffer_end: int = 200,
        callback_delay: float = 0.05,
        max_prompt_attempts: int = 100,
    ) -> None:
        self.format = format
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.device_index = device_index
        self.listener: Optional[MyListener] = None
        self.started = False
        self.audio: Optional[pyaudio.PyAudio] = None
        self.first_call = True
        self.frames: List[bytes] = []
        self.task: Optional[sched.scheduler] = None
        self.stream: Optional[RecorderStream] = None
        self.trim_silence_threshold = trim_silence_threshold
        self.trim_buffer_start = trim_buffer_start
        self.trim_buffer_end = trim_buffer_end
        self.callback_delay = callback_delay
        self.max_prompt_attempts = max_prompt_attempts

    def _audio(self) -> pyaudio.PyAudio:
        self._init_pyaudio()
        if self.audio is None:
            raise RuntimeError("PyAudio failed to initialize.")
        return self.audio

    def _listener(self) -> MyListener:
        if self.listener is None:
            raise RuntimeError("Recorder listener has not been initialized.")
        return self.listener

    def _scheduler(self) -> sched.scheduler:
        if self.task is None:
            raise RuntimeError("Recorder scheduler has not been initialized.")
        return self.task

    def _channels(self) -> int:
        if self.channels is None:
            raise RuntimeError("Recorder channel count has not been selected.")
        return self.channels

    def _stream(self) -> RecorderStream:
        if self.stream is None:
            raise RuntimeError("Recorder stream has not been opened.")
        return self.stream

    def _trigger_set_device(self) -> None:
        self._init_pyaudio()

        if self.device_index is None:
            self._set_device()

        if self.channels is None:
            if self.device_index is None:
                raise RuntimeError("Recorder device index has not been selected.")
            self._set_channels_from_device_index(self.device_index)

    def _init_pyaudio(self) -> None:
        if self.audio is None:
            self.audio = pyaudio.PyAudio()

    def _record(self, path: str) -> None:
        self._trigger_set_device()
        self.frames = []
        self.listener = MyListener()
        self.listener.start()

        for message in RECORDING_START_MESSAGES:
            print(message)
        if self.first_call:
            for message in FIRST_RECORDING_MESSAGES:
                print(message)

        for message in RECORDING_END_MESSAGES:
            print(message)
        self.task = sched.scheduler(time.time, time.sleep)
        self.event = self.task.enter(self.callback_delay, 1, self._record_task, (path,))
        self.task.run()

    def _set_device(self) -> None:
        # Prompt the user to select an input device from the PyAudio host API.
        print("-------------------------device list-------------------------")
        n_devices = self._device_count()
        if not isinstance(n_devices, int):
            raise RuntimeError("PyAudio did not report an integer device count.")
        for i in range(n_devices):
            device_info = self._device_info(i)
            max_input_channels = device_info.get("maxInputChannels")
            if isinstance(max_input_channels, (int, float)) and max_input_channels > 0:
                print(
                    "Input Device id ",
                    i,
                    " - ",
                    device_info.get("name"),
                )

        print("-------------------------------------------------------------")
        print("Please select an input device id to record from:")

        try:
            self.device_index = int(input())
            device_name = self._device_info(self.device_index).get("name")
            self._set_channels_from_device_index(self.device_index)
            self._set_rate_from_device_index(self.device_index)
            print("Selected device:", device_name)
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            exit()
        except (ValueError, OSError):
            print("Invalid device index. Please try again.")
            self._set_device()

    def _device_count(self) -> object:
        return self._audio().get_host_api_info_by_index(HOST_API_INDEX).get("deviceCount")

    def _device_info(self, device_index: int) -> Mapping[str, object]:
        device_info = self._audio().get_device_info_by_host_api_device_index(HOST_API_INDEX, device_index)
        if not isinstance(device_info, Mapping):
            raise RuntimeError("PyAudio did not report device info.")
        return device_info

    def _set_channels_from_device_index(self, device_index: int) -> None:
        channels_from_device = self._device_info(device_index).get("maxInputChannels")
        if not isinstance(channels_from_device, int):
            raise RuntimeError("PyAudio did not report integer max input channels.")
        if self.channels is None:
            self.channels = channels_from_device
        else:
            self.channels = min(self.channels, channels_from_device)

    def _set_rate_from_device_index(self, device_index: int) -> None:
        rate_from_device = self._device_info(device_index).get("defaultSampleRate")
        if not isinstance(rate_from_device, (int, float)):
            raise RuntimeError("PyAudio did not report a numeric sample rate.")
        if self.rate is None:
            self.rate = int(rate_from_device)
        else:
            self.rate = int(min(self.rate, rate_from_device))

    def _record_task(self, path: str) -> None:
        listener = self._listener()
        task = self._scheduler()
        if listener.key_pressed and not self.started:
            # Start the recording
            self.stream = self._audio().open(
                format=self.format,
                channels=self._channels(),
                rate=self.rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk,
                stream_callback=self.callback,
            )
            stream = self._stream()
            print("Stream active:", stream.is_active())
            self.started = True
            print("start Stream")

            task.enter(self.callback_delay, 1, self._record_task, (path,))

        elif not listener.key_pressed and self.started:
            stream = self._stream()
            stream.stop_stream()
            stream.close()

            print("Finished recording, saving to", path)

            # Save wav
            wav_path = str(Path(path).with_suffix(".wav"))

            wf = wave.open(wav_path, "wb")
            wf.setnchannels(self._channels())
            wf.setsampwidth(self._audio().get_sample_size(self.format))
            wf.setframerate(self.rate)

            self._audio().terminate()
            self.audio = None
            self.started = False
            self.first_call = False

            # Remove 1 second from the end of frames
            self.frames = self.frames[: -int(self.rate * 0.5 / self.chunk)]

            wf.writeframes(b"".join(self.frames))
            wf.close()
            trim_silence(
                AudioSegment.from_wav(wav_path),
                silence_threshold=self.trim_silence_threshold,
                buffer_start=self.trim_buffer_start,
                buffer_end=self.trim_buffer_end,
            ).export(wav_path, format="wav")
            wav2mp3(wav_path)

            for event in list(task.queue):
                task.cancel(event)

            return

        # Reschedule the recorder function in 100 ms.
        task.enter(self.callback_delay, 1, self._record_task, (path,))

    def callback(
        self,
        in_data: bytes,
        frame_count: int,
        time_info: Dict[str, float],
        status: int,
    ) -> Tuple[bytes, int]:
        self.frames.append(in_data)
        return (in_data, pyaudio.paContinue)

    def record(self, path: str, message: Optional[str] = None) -> None:
        if message is not None:
            print(message)
        self._record(path)

        for _ in range(self.max_prompt_attempts):
            print(
                """Press...
 l to [l]isten to the recording
 r to [r]e-record
 a to [a]ccept the recording
"""
            )
            try:
                key = input()[-1].lower()
                if key == "l":
                    audio = AudioSegment.from_file(path)
                    play(audio)
                elif key == "r":
                    if message is not None:
                        print(message)

                    self._record(path)
                elif key == "a":
                    return
                else:
                    print("Invalid input")
            except KeyboardInterrupt:
                print("KeyboardInterrupt")
                exit()

        raise RuntimeError("Recorder prompt did not receive an accept choice.")
