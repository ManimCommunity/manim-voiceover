import os
from pathlib import Path
import time
import wave
import sys
import sched

from manim_voiceover.helper import wav2mp3

try:
    from pynput import keyboard
    import pyaudio
except ImportError:
    print(
        'Missing packages. Run `pip install "manim-voiceover[recorder]"` to use RecorderService.'
    )

CALLBACK_DELAY = 0.1


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
    ):
        self.format = format
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.device_index = device_index
        self.listener = None
        self.started = None
        self.audio = None

    def record(self, path):
        self.audio = pyaudio.PyAudio()
        if self.device_index is None:
            self._set_device()

        if self.channels is None:
            self._set_channels_from_device_index(self.device_index)

        self.frames = []
        self.listener = MyListener()
        self.listener.start()

        print("Press and hold the 'r' key to begin recording")
        print("Release the 'r' key to end recording")
        self.task = sched.scheduler(time.time, time.sleep)
        self.event = self.task.enter(CALLBACK_DELAY, 1, self._record_task, ([path]))
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

            self.task.enter(CALLBACK_DELAY, 1, self._record_task, ([path]))

        elif not self.listener.key_pressed and self.started:
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()
            self.started = None

            print("Finished recording, saving to", path)

            # Save wav
            wav_path = str(Path(path).with_suffix(".wav"))

            wf = wave.open(wav_path, "wb")
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)

            wf.writeframes(b"".join(self.frames))
            wf.close()

            wav2mp3(wav_path)

            for e in self.task._queue:
                self.task.cancel(e)

            return

        # Reschedule the recorder function in 100 ms.
        self.task.enter(CALLBACK_DELAY, 1, self._record_task, ([path]))

    def callback(self, in_data, frame_count, time_info, status):
        self.frames.append(in_data)
        return (in_data, pyaudio.paContinue)
