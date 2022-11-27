import os
import time
import wave
import sys
import sched
from pathlib import Path
from pydub import AudioSegment
from manim import logger

from manim_voiceover.helper import trim_silence, wav2mp3

try:
    from pynput import keyboard
    import pyaudio
    import playsound
except ImportError:
    logger.error(
        'Missing packages. Run `pip install "manim-voiceover[recorder]"` to use RecorderService.'
    )


class MyListener(keyboard.Listener):
    def __init__(self):
        super(MyListener, self).__init__(self.on_press, self.on_release)
        self.key_pressed = None

    def on_press(self, key):
        if not hasattr(key, "char"):
            return True

        if key.char == "r":
            self.key_pressed = True

        return True

    def on_release(self, key):
        if not hasattr(key, "char"):
            return True

        if key.char == "r":
            self.key_pressed = False

        return True


class Recorder:
    def __init__(
        self,
        format: int = pyaudio.paInt16,
        channels: int = None,
        rate: int = 44100,
        chunk: int = 512,
        device_index: int = None,
        trim_silence_threshold: float = -40.0,
        trim_buffer_start: int = 200,
        trim_buffer_end: int = 200,
        callback_delay: float = 0.05,
    ):
        self.format = format
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.device_index = device_index
        self.listener = None
        self.started = None
        self.audio = None
        self.first_call = True
        self.trim_silence_threshold = trim_silence_threshold
        self.trim_buffer_start = trim_buffer_start
        self.trim_buffer_end = trim_buffer_end
        self.callback_delay = callback_delay

    def _trigger_set_device(self):
        self._init_pyaudio()

        if self.device_index is None:
            self._set_device()

        if self.channels is None:
            self._set_channels_from_device_index(self.device_index)

    def _init_pyaudio(self):
        if self.audio is None:
            self.audio = pyaudio.PyAudio()

    def _record(self, path):
        self._init_pyaudio()

        if self.device_index is None:
            self._set_device()

        if self.channels is None:
            self._set_channels_from_device_index(self.device_index)

        self.frames = []
        self.listener = MyListener()
        self.listener.start()

        print("Press and hold the 'r' key to begin recording")
        if self.first_call:
            print("Wait for 1 second, then start speaking.")
            print("Wait for at least 1 second after you finish speaking.")
            print("This is to eliminate any sounds that may come from your keyboard.")
            print("The silence at the beginning and end will be trimmed automatically.")
            print(
                "You can adjust this setting using the `trim_silence_threshold` argument."
            )
            print("These instructions are only shown once.")

        print("Release the 'r' key to end recording")
        self.task = sched.scheduler(time.time, time.sleep)
        self.event = self.task.enter(
            self.callback_delay, 1, self._record_task, ([path])
        )
        self.task.run()

        return

    def _set_device(self):
        "Get the device index from the user."
        print("-------------------------device list-------------------------")
        info = self.audio.get_host_api_info_by_index(0)
        n_devices = info.get("deviceCount")
        for i in range(0, n_devices):
            if (
                self.audio.get_device_info_by_host_api_device_index(0, i).get(
                    "maxInputChannels"
                )
            ) > 0:
                print(
                    "Input Device id ",
                    i,
                    " - ",
                    self.audio.get_device_info_by_host_api_device_index(0, i).get(
                        "name"
                    ),
                )

        print("-------------------------------------------------------------")
        print("Please select an input device id to record from:")

        try:
            self.device_index = int(input())
            device_name = self.audio.get_device_info_by_host_api_device_index(
                0, self.device_index
            ).get("name")
            self._set_channels_from_device_index(self.device_index)
            print("Selected device:", device_name)
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            exit()
        except:
            print("Invalid device index. Please try again.")
            self._set_device()

        return

    def _set_channels_from_device_index(self, device_index):
        self.channels = self.audio.get_device_info_by_host_api_device_index(
            0, device_index
        ).get("maxInputChannels")

    def _record_task(self, path):
        if self.listener.key_pressed and not self.started:
            # Start the recording
            try:
                self.stream = self.audio.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    frames_per_buffer=self.chunk,
                    stream_callback=self.callback,
                )
                print("Stream active:", self.stream.is_active())
                self.started = True
                print("start Stream")
            except:
                raise

            self.task.enter(self.callback_delay, 1, self._record_task, ([path]))

        elif not self.listener.key_pressed and self.started:
            self.stream.stop_stream()
            self.stream.close()

            print("Finished recording, saving to", path)

            # Save wav
            wav_path = str(Path(path).with_suffix(".wav"))

            wf = wave.open(wav_path, "wb")
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)

            self.audio.terminate()
            self.audio = None
            self.started = None
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

            for e in self.task._queue:
                self.task.cancel(e)

            return

        # Reschedule the recorder function in 100 ms.
        self.task.enter(self.callback_delay, 1, self._record_task, ([path]))

    def callback(self, in_data, frame_count, time_info, status):
        self.frames.append(in_data)
        return (in_data, pyaudio.paContinue)

    def record(self, path: str, message: str = None):
        if message is not None:
            print(message)
        self._record(path)

        while True:
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
                    playsound.playsound(path)
                elif key == "r":
                    if message is not None:
                        print(message)

                    self._record(path)
                elif key == "a":
                    break
                else:
                    print("Invalid input")
            except KeyboardInterrupt:
                print("KeyboardInterrupt")
                exit()
