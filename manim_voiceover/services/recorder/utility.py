import os
import time
import wave
import sys
import sched
from pathlib import Path
from pydub import AudioSegment
from manim import logger

from manim_voiceover.helper import trim_silence, wav2mp3
from readchar import readchar

import pyaudio
try:
    import playsound
except:
    playsound = None

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

    def _init_recording(self):
        self._init_pyaudio()

        if self.device_index is None:
            self._set_device()

        if self.channels is None:
            self._set_channels_from_device_index(self.device_index)

        self.frames = []

        
    def _set_device(self):
        "Get the device index from the user."
        print("-------------------------device list-------------------------")
        info = self.audio.get_host_api_info_by_index(0)
        n_devices = info.get("deviceCount")
        valid_devices = []
        for i in range(0, n_devices):
            if (
                self.audio.get_device_info_by_host_api_device_index(0, i).get(
                    "maxInputChannels"
                )
            ) > 0:
                valid_devices.append(i)
                print(
                    "Input Device id ",
                    i,
                    " - ",
                    self.audio.get_device_info_by_host_api_device_index(0, i).get(
                        "name"
                    ),
                )
        print("-------------------------------------------------------------")

        if len(valid_devices) == 1:
            # Skip the device selection as there is only one option
            self.device_index = valid_devices[0]
            return
        
        print("Please select an input device id to record from:")

        try:
            self.device_index = int(input())
            assert self.device_index in valid_devices
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

    def _start_recording_stream(self):
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

    def _stop_recording_stream(self, path):
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

            # Remove 0.25 second from the end of the recording
            half_second = max(1, int((self.rate / 4) / self.chunk))
            self.frames = self.frames[half_second:-half_second]

            wf.writeframes(b"".join(self.frames))
            wf.close()
            trim_silence(
                AudioSegment.from_wav(wav_path),
                silence_threshold=self.trim_silence_threshold,
                buffer_start=self.trim_buffer_start,
                buffer_end=self.trim_buffer_end,
            ).export(wav_path, format="wav")
            wav2mp3(wav_path)


    def callback(self, in_data, frame_count, time_info, status):
        self.frames.append(in_data)
        return (in_data, pyaudio.paContinue)

    def record(self, path: str, message: str = None):
        if self.first_call:
            print('### Instructions ###')
            print("Press and hold the 'r' key to begin recording")
            print("Wait for 1 second, then start speaking.")
            print("Wait for at least 1 second after you finish speaking.")
            print("This is to eliminate any sounds that may come from your keyboard.")
            print("The silence at the beginning and end will be trimmed automatically.")
            print(
                "You can adjust this setting using the `trim_silence_threshold` argument."
            )
            print("Press the 's' key to end recording")
        else:
            print('Press...')
            print("  r to [r]ecord")
            print("  s to [s]top recording")
        print(message)            
        try:
            key = 'r'
            while key != 'a':
                key = readchar().lower()
                if key == 'r':
                    self._init_recording()
                    self._start_recording_stream()
                    if readchar().lower() != 's':
                        print('Press S to stop recording')
                        while readchar().lower() != 's':
                            pass
                    self._stop_recording_stream(path)
                    
                    if playsound is not None:
                        print('  l to [l]isten to the recording')
                    print("  r to [r]ecord again")
                    print("  a to [a]ccept the recording")
                elif key == 'l':
                    if playsound is None:
                        print('Playsound not available')
                    else:
                        playsound.playsound(path)
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            exit()
