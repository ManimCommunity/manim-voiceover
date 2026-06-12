import time
from types import SimpleNamespace

import pytest
from manim_voiceover.services.recorder import RecorderService
from manim_voiceover.services.recorder.utility import (
    FIRST_RECORDING_MESSAGES,
    HOST_API_INDEX,
    RECORDING_END_MESSAGES,
    RECORDING_START_MESSAGES,
    MyListener,
    Recorder,
    _create_keyboard_listener,
)


@pytest.fixture
def forbid_real_pyaudio(monkeypatch):
    monkeypatch.setattr(
        "manim_voiceover.services.recorder.utility.pyaudio.PyAudio",
        lambda: pytest.fail("Recorder test should not create a real PyAudio instance."),
    )


class FakeAudio:
    def __init__(self):
        self.terminated = False
        self.open_kwargs = []
        self.device_queries = []
        self.sample_size_requests = []

    def get_host_api_info_by_index(self, index):
        return {"deviceCount": 2}

    def get_device_info_by_host_api_device_index(self, host_api_index, device_index):
        self.device_queries.append((host_api_index, device_index))
        return {"maxInputChannels": 2, "name": f"mic-{device_index}", "defaultSampleRate": 44100.0}

    def open(self, **kwargs):
        self.open_kwargs.append(kwargs)
        return FakeStream()

    def get_sample_size(self, format):
        self.sample_size_requests.append(format)
        return 2

    def terminate(self):
        self.terminated = True


class DeviceListAudio(FakeAudio):
    def __init__(self):
        super().__init__()
        self.devices = [
            {"maxInputChannels": 0, "name": "output-only", "defaultSampleRate": 48000.0},
            {"maxInputChannels": 2, "name": "studio-mic", "defaultSampleRate": 44100.0},
        ]
        self.host_queries = []

    def get_host_api_info_by_index(self, index):
        assert index == HOST_API_INDEX
        self.host_queries.append(index)
        return {"deviceCount": len(self.devices)}

    def get_device_info_by_host_api_device_index(self, host_api_index, device_index):
        assert host_api_index == HOST_API_INDEX
        self.device_queries.append((host_api_index, device_index))
        return self.devices[device_index]


class FakeStream:
    def __init__(self):
        self.closed = False

    def is_active(self):
        return True

    def stop_stream(self):
        self.stopped = True

    def close(self):
        self.closed = True


class FakeTask:
    def __init__(self):
        self.entered = []
        self.queue = []

    def enter(self, delay, priority, action, argument):
        event = SimpleNamespace(delay=delay, priority=priority, action=action, argument=argument)
        self.entered.append(event)
        self.queue.append(event)
        return event

    def cancel(self, event):
        self.queue.remove(event)


class FakeWave:
    def __init__(self):
        self.frames = b""

    def setnchannels(self, channels):
        self.channels = channels

    def setsampwidth(self, width):
        self.width = width

    def setframerate(self, rate):
        self.rate = rate

    def writeframes(self, frames):
        self.frames = frames

    def close(self):
        self.closed = True


def test_recorder_constructor_defaults():
    recorder = Recorder()
    assert recorder.format == 8
    assert recorder.channels is None
    assert recorder.rate == 44100
    assert recorder.chunk == 512
    assert recorder.device_index is None
    assert recorder.listener is None
    assert recorder.started is False
    assert recorder.audio is None
    assert recorder.first_call is True
    assert recorder.frames == []
    assert recorder.task is None
    assert recorder.stream is None
    assert recorder.trim_silence_threshold == -40.0
    assert recorder.trim_buffer_start == 200
    assert recorder.trim_buffer_end == 200
    assert recorder.callback_delay == 0.05
    assert recorder.max_prompt_attempts == 100


def test_listener_tracks_record_key():
    listener = MyListener()
    assert listener.key_pressed is False
    assert listener._keyboard_listener is None
    listener.on_press(SimpleNamespace(char="r"))
    assert listener.key_pressed is True
    listener.on_release(SimpleNamespace(char="r"))
    assert listener.key_pressed is False

    listener.on_press(SimpleNamespace(char="x"))
    assert listener.key_pressed is False
    listener.on_release(SimpleNamespace(char="x"))
    assert listener.key_pressed is False

    listener.on_press(SimpleNamespace(r=True))
    assert listener.key_pressed is True
    listener.on_release(SimpleNamespace(shift_r=True))
    assert listener.key_pressed is False
    listener.on_press(SimpleNamespace(shift_r=True))
    assert listener.key_pressed is True
    listener.on_release(SimpleNamespace(r=True))
    assert listener.key_pressed is False
    listener.on_press(SimpleNamespace(char="shift_r"))
    assert listener.key_pressed is True
    listener.on_release(SimpleNamespace(char="shift_r"))
    assert listener.key_pressed is False
    assert listener.on_press(object()) is True
    assert listener.on_release(object()) is True


def test_keyboard_listener_factory_and_start(monkeypatch):
    created = []
    started = []

    class FakeListener:
        def __init__(self, on_press, on_release):
            created.append((on_press, on_release))

        def start(self):
            started.append("started")

    imported_modules = []

    def import_module(name):
        imported_modules.append(name)
        return SimpleNamespace(Listener=FakeListener)

    monkeypatch.setattr("manim_voiceover.services.recorder.utility.importlib.import_module", import_module)

    def on_press(key):
        return True

    def on_release(key):
        return True

    listener = _create_keyboard_listener(on_press, on_release)
    assert isinstance(listener, FakeListener)
    assert created == [(on_press, on_release)]
    assert imported_modules == ["pynput.keyboard"]

    my_listener = MyListener()
    my_listener.start()
    assert isinstance(my_listener._keyboard_listener, FakeListener)
    assert created[-1] == (my_listener.on_press, my_listener.on_release)
    assert started == ["started"]

    def missing(module):
        raise ImportError(module)

    monkeypatch.setattr("manim_voiceover.services.recorder.utility.importlib.import_module", missing)
    with pytest.raises(ImportError) as exc_info:
        _create_keyboard_listener(on_press, on_release)
    assert (
        str(exc_info.value) == 'Missing or unusable pynput keyboard backend. Run `pip install "manim-voiceover[recorder]"` '
        "and make sure a supported display backend is available."
    )

    monkeypatch.setattr(
        "manim_voiceover.services.recorder.utility.importlib.import_module",
        lambda name: SimpleNamespace(Listener=object()),
    )
    with pytest.raises(RuntimeError) as exc_info:
        _create_keyboard_listener(on_press, on_release)
    assert str(exc_info.value) == "pynput.keyboard.Listener is not callable."


def test_recorder_guard_helpers_raise():
    recorder = Recorder(channels=None, device_index=None)
    with pytest.raises(RuntimeError) as exc_info:
        recorder._listener()
    assert str(exc_info.value) == "Recorder listener has not been initialized."
    with pytest.raises(RuntimeError) as exc_info:
        recorder._scheduler()
    assert str(exc_info.value) == "Recorder scheduler has not been initialized."
    with pytest.raises(RuntimeError) as exc_info:
        recorder._channels()
    assert str(exc_info.value) == "Recorder channel count has not been selected."
    with pytest.raises(RuntimeError) as exc_info:
        recorder._stream()
    assert str(exc_info.value) == "Recorder stream has not been opened."

    listener = MyListener()
    task = FakeTask()
    stream = FakeStream()
    recorder.listener = listener
    recorder.task = task
    recorder.channels = 1
    recorder.stream = stream
    assert recorder._listener() is listener
    assert recorder._scheduler() is task
    assert recorder._channels() == 1
    assert recorder._stream() is stream


def test_recorder_init_pyaudio_uses_factory(monkeypatch):
    recorder = Recorder(channels=1, device_index=0)
    fake_audio = FakeAudio()
    monkeypatch.setattr("manim_voiceover.services.recorder.utility.pyaudio.PyAudio", lambda: fake_audio)
    recorder._init_pyaudio()
    assert recorder.audio is fake_audio
    recorder._init_pyaudio()
    assert recorder.audio is fake_audio


def test_recorder_audio_helper_requires_initialized_backend(monkeypatch):
    recorder = Recorder(channels=1, device_index=0)
    monkeypatch.setattr("manim_voiceover.services.recorder.utility.pyaudio.PyAudio", lambda: None)

    with pytest.raises(RuntimeError) as exc_info:
        recorder._audio()

    assert str(exc_info.value) == "PyAudio failed to initialize."


def test_recorder_device_helpers_delegate_to_host_api(forbid_real_pyaudio):
    recorder = Recorder()
    audio = DeviceListAudio()
    recorder.audio = audio

    assert recorder._device_count() == 2
    assert recorder._device_info(1) == {
        "maxInputChannels": 2,
        "name": "studio-mic",
        "defaultSampleRate": 44100.0,
    }
    assert audio.host_queries == [HOST_API_INDEX]
    assert audio.device_queries == [(HOST_API_INDEX, 1)]

    class BadDeviceInfoAudio(DeviceListAudio):
        def get_device_info_by_host_api_device_index(self, host_api_index, device_index):
            super().get_device_info_by_host_api_device_index(host_api_index, device_index)
            return []

    bad_recorder = Recorder()
    bad_recorder.audio = BadDeviceInfoAudio()
    with pytest.raises(RuntimeError) as exc_info:
        bad_recorder._device_info(1)
    assert str(exc_info.value) == "PyAudio did not report device info."


def test_recorder_sets_device_from_input(monkeypatch, forbid_real_pyaudio):
    recorder = Recorder(channels=None, device_index=None)
    audio = DeviceListAudio()
    recorder.audio = audio
    printed = []
    monkeypatch.setattr("builtins.input", lambda: "1")
    monkeypatch.setattr("builtins.print", lambda *args: printed.append(args))
    recorder._trigger_set_device()
    assert recorder.device_index == 1
    assert recorder.channels == 2
    assert recorder.rate == 44100
    assert audio.host_queries == [HOST_API_INDEX]
    assert (0, 1) in audio.device_queries
    assert printed == [
        ("-------------------------device list-------------------------",),
        ("Input Device id ", 1, " - ", "studio-mic"),
        ("-------------------------------------------------------------",),
        ("Please select an input device id to record from:",),
        ("Selected device:", "studio-mic"),
    ]


def test_recorder_lists_one_channel_input_devices(monkeypatch, forbid_real_pyaudio):
    class OneChannelAudio(DeviceListAudio):
        def __init__(self):
            super().__init__()
            self.devices = [
                {"maxInputChannels": 1, "name": "headset-mic", "defaultSampleRate": 16000.0},
            ]

    recorder = Recorder(channels=None, device_index=None)
    recorder.audio = OneChannelAudio()
    printed = []
    monkeypatch.setattr("builtins.input", lambda: "0")
    monkeypatch.setattr("builtins.print", lambda *args: printed.append(args))

    recorder._set_device()

    assert recorder.device_index == 0
    assert recorder.channels == 1
    assert recorder.rate == 16000
    assert ("Input Device id ", 0, " - ", "headset-mic") in printed


def test_recorder_set_device_retries_invalid_input(monkeypatch, forbid_real_pyaudio):
    recorder = Recorder(channels=None, device_index=None)
    recorder.audio = DeviceListAudio()
    printed = []
    monkeypatch.setattr("builtins.input", iter(["bad", "1"]).__next__)
    monkeypatch.setattr("builtins.print", lambda *args: printed.append(args))

    recorder._set_device()

    assert recorder.device_index == 1
    assert recorder.channels == 2
    assert recorder.rate == 44100
    assert ("Invalid device index. Please try again.",) in printed
    assert printed.count(("Selected device:", "studio-mic")) == 1


def test_recorder_device_error_paths(monkeypatch, forbid_real_pyaudio):
    recorder = Recorder(channels=None, device_index=0)
    recorder.audio = FakeAudio()
    recorder._trigger_set_device()
    assert recorder.channels == 2
    assert recorder.audio.device_queries == [(HOST_API_INDEX, 0)]

    class BadAudio(FakeAudio):
        def get_host_api_info_by_index(self, index):
            return {"deviceCount": "two"}

    bad = Recorder()
    bad.audio = BadAudio()
    with pytest.raises(RuntimeError) as exc_info:
        bad._set_device()
    assert str(exc_info.value) == "PyAudio did not report an integer device count."

    class BadDeviceInfoAudio(FakeAudio):
        def get_device_info_by_host_api_device_index(self, host_api_index, device_index):
            return []

    bad_device_info = Recorder()
    bad_device_info.audio = BadDeviceInfoAudio()
    with pytest.raises(RuntimeError, match="PyAudio did not report device info."):
        bad_device_info._device_info(0)

    class MissingChannelsAudio(FakeAudio):
        def get_device_info_by_host_api_device_index(self, host_api_index, device_index):
            return {"maxInputChannels": "bad", "name": "mic", "defaultSampleRate": 44100.0}

    bad_channels = Recorder()
    bad_channels.audio = MissingChannelsAudio()
    with pytest.raises(RuntimeError) as exc_info:
        bad_channels._set_channels_from_device_index(0)
    assert str(exc_info.value) == "PyAudio did not report integer max input channels."

    limited_channels = Recorder(channels=4)
    limited_channels.audio = FakeAudio()
    limited_channels._set_channels_from_device_index(0)
    assert limited_channels.channels == 2

    class MissingRateAudio(FakeAudio):
        def get_device_info_by_host_api_device_index(self, host_api_index, device_index):
            return {"maxInputChannels": 1, "name": "mic", "defaultSampleRate": "fast"}

    bad_rate = Recorder()
    bad_rate.audio = MissingRateAudio()
    with pytest.raises(RuntimeError) as exc_info:
        bad_rate._set_rate_from_device_index(0)
    assert str(exc_info.value) == "PyAudio did not report a numeric sample rate."

    limited_rate = Recorder(rate=48000)
    limited_rate.audio = FakeAudio()
    limited_rate._set_rate_from_device_index(0)
    assert limited_rate.rate == 44100

    default_rate = Recorder(rate=None)
    default_rate.audio = FakeAudio()
    default_rate._set_rate_from_device_index(0)
    assert default_rate.rate == 44100

    printed = []
    monkeypatch.setattr("builtins.print", lambda *args: printed.append(args))
    monkeypatch.setattr("builtins.input", lambda: (_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(SystemExit):
        recorder._set_device()
    assert ("KeyboardInterrupt",) in printed


def test_recorder_trigger_set_device_requires_selected_device(forbid_real_pyaudio):
    recorder = Recorder(channels=None, device_index=None)
    recorder.audio = FakeAudio()
    recorder._set_device = lambda: None
    with pytest.raises(RuntimeError) as exc_info:
        recorder._trigger_set_device()
    assert str(exc_info.value) == "Recorder device index has not been selected."


def test_recorder_record_sets_up_scheduler(monkeypatch, tmp_path, forbid_real_pyaudio):
    recorder = Recorder(channels=1, device_index=0, callback_delay=0.01)
    recorder.audio = FakeAudio()
    recorder.frames = [b"old"]
    printed = []
    scheduler_args = []

    class FakeListener:
        def start(self):
            self.started = True

    class OneShotScheduler(FakeTask):
        def run(self):
            self.ran = True

    monkeypatch.setattr("manim_voiceover.services.recorder.utility.MyListener", FakeListener)

    def make_scheduler(time_fn, sleep_fn):
        scheduler_args.append((time_fn, sleep_fn))
        return OneShotScheduler()

    monkeypatch.setattr("manim_voiceover.services.recorder.utility.sched.scheduler", make_scheduler)
    monkeypatch.setattr("builtins.print", lambda *args: printed.append(args))
    recorder._record(str(tmp_path / "recording.mp3"))

    assert recorder.frames == []
    assert recorder.listener.started is True
    assert recorder.task.ran is True
    assert scheduler_args == [(time.time, time.sleep)]
    assert recorder.event == recorder.task.entered[0]
    assert recorder.task.entered[0].delay == 0.01
    assert recorder.task.entered[0].priority == 1
    assert recorder.task.entered[0].action == recorder._record_task
    assert recorder.task.entered[0].argument == (str(tmp_path / "recording.mp3"),)
    assert printed == [(message,) for message in RECORDING_START_MESSAGES + FIRST_RECORDING_MESSAGES + RECORDING_END_MESSAGES]


def test_recorder_record_task_start_and_stop(monkeypatch, tmp_path, forbid_real_pyaudio):
    recorder = Recorder(channels=1, device_index=0, rate=12, chunk=2)
    audio = FakeAudio()
    recorder.audio = audio
    recorder.listener = SimpleNamespace(key_pressed=True)
    recorder.task = FakeTask()
    recorder.frames = [b"a"] * 12
    fake_wave = FakeWave()
    exported = []
    printed = []
    trim_calls = []
    wave_open_calls = []
    from_wav_paths = []

    monkeypatch.setattr(
        "manim_voiceover.services.recorder.utility.wave.open",
        lambda path, mode: wave_open_calls.append((path, mode)) or fake_wave,
    )
    monkeypatch.setattr(
        "manim_voiceover.services.recorder.utility.trim_silence",
        lambda segment, **kwargs: (
            trim_calls.append((segment, kwargs))
            or SimpleNamespace(export=lambda path, format: exported.append((path, format)))
        ),
    )
    monkeypatch.setattr(
        "manim_voiceover.services.recorder.utility.AudioSegment.from_wav",
        lambda path: from_wav_paths.append(path) or "wav-audio",
    )
    monkeypatch.setattr("manim_voiceover.services.recorder.utility.wav2mp3", lambda path: exported.append(path))
    monkeypatch.setattr("builtins.print", lambda *args: printed.append(args))

    output_path = str(tmp_path / "recording.mp3")
    recorder._record_task(output_path)
    assert recorder.started is True
    assert recorder.task.entered
    assert len(audio.open_kwargs) == 1
    assert audio.open_kwargs[-1] == {
        "format": recorder.format,
        "channels": 1,
        "rate": 12,
        "input": True,
        "input_device_index": 0,
        "frames_per_buffer": 2,
        "stream_callback": recorder.callback,
    }
    assert ("start Stream",) in printed
    assert ("Stream active:", True) in printed
    assert len(recorder.task.entered) == 2
    start_event = recorder.task.entered[-2]
    assert start_event.delay == 0.05
    assert start_event.priority == 1
    assert start_event.action == recorder._record_task
    assert start_event.argument == (output_path,)
    start_reschedule_event = recorder.task.entered[-1]
    assert start_reschedule_event.delay == 0.05
    assert start_reschedule_event.priority == 1
    assert start_reschedule_event.action == recorder._record_task
    assert start_reschedule_event.argument == (output_path,)

    recorder._record_task(output_path)
    assert len(audio.open_kwargs) == 1
    repeat_event = recorder.task.entered[-1]
    assert repeat_event.delay == 0.05
    assert repeat_event.priority == 1
    assert repeat_event.action == recorder._record_task
    assert repeat_event.argument == (output_path,)

    recorder.listener.key_pressed = False
    recorder._record_task(output_path)
    assert recorder.started is False
    assert recorder.audio is None
    assert audio.terminated is True
    assert fake_wave.closed is True
    assert fake_wave.channels == 1
    assert fake_wave.width == 2
    assert fake_wave.rate == 12
    assert fake_wave.frames == b"aaaaaaaaa"
    assert audio.sample_size_requests == [recorder.format]
    wav_path = str(tmp_path / "recording.wav")
    assert wave_open_calls == [(wav_path, "wb")]
    assert from_wav_paths == [wav_path]
    assert trim_calls == [
        (
            "wav-audio",
            {
                "silence_threshold": -40.0,
                "buffer_start": 200,
                "buffer_end": 200,
            },
        )
    ]
    assert exported == [(wav_path, "wav"), wav_path]
    assert ("Finished recording, saving to", output_path) in printed
    assert recorder.first_call is False
    assert recorder.task.queue == []


def test_recorder_callback_appends_frame():
    recorder = Recorder()
    data, status = recorder.callback(b"frame", 1, {}, 0)
    assert data == b"frame"
    assert status == 0
    assert recorder.frames == [b"frame"]


def test_recorder_record_prompt_loop(monkeypatch, tmp_path):
    recorder = Recorder(channels=1, device_index=0)
    recorded = []
    played = []
    printed = []
    loaded_paths = []
    monkeypatch.setattr(recorder, "_record", lambda path: recorded.append(path))
    monkeypatch.setattr("builtins.input", iter(["l", "r", "a"]).__next__)
    monkeypatch.setattr(
        "manim_voiceover.services.recorder.utility.AudioSegment.from_file",
        lambda path: loaded_paths.append(path) or "audio",
    )
    monkeypatch.setattr("manim_voiceover.services.recorder.utility.play", lambda audio: played.append(audio))
    monkeypatch.setattr("builtins.print", lambda *args: printed.append(args))

    recorder.record(str(tmp_path / "recording.mp3"), message="say it")
    assert recorded == [str(tmp_path / "recording.mp3"), str(tmp_path / "recording.mp3")]
    assert loaded_paths == [str(tmp_path / "recording.mp3")]
    assert played == ["audio"]
    assert printed.count(("say it",)) == 2
    assert (
        printed.count(
            (
                """Press...
 l to [l]isten to the recording
 r to [r]e-record
 a to [a]ccept the recording
""",
            )
        )
        == 3
    )


def test_recorder_record_invalid_and_keyboard_interrupt(monkeypatch, tmp_path):
    recorder = Recorder(channels=1, device_index=0)
    printed = []
    monkeypatch.setattr(recorder, "_record", lambda path: None)
    monkeypatch.setattr("builtins.print", lambda *args: printed.append(args))
    monkeypatch.setattr("builtins.input", iter(["x", "a"]).__next__)
    recorder.record(str(tmp_path / "recording.mp3"))
    assert ("Invalid input",) in printed

    monkeypatch.setattr("builtins.input", lambda: (_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(SystemExit):
        recorder.record(str(tmp_path / "recording.mp3"))
    assert ("KeyboardInterrupt",) in printed


def test_recorder_record_invalid_choices_are_bounded(monkeypatch, tmp_path):
    recorder = Recorder(channels=1, device_index=0, max_prompt_attempts=1)
    monkeypatch.setattr(recorder, "_record", lambda path: None)
    monkeypatch.setattr("builtins.input", lambda: "x")

    with pytest.raises(RuntimeError) as exc_info:
        recorder.record(str(tmp_path / "recording.mp3"))
    assert str(exc_info.value) == "Recorder prompt did not receive an accept choice."


def test_recorder_record_accepts_accept_choice_once(monkeypatch, tmp_path):
    recorder = Recorder(channels=1, device_index=0)
    monkeypatch.setattr(recorder, "_record", lambda path: None)
    choices = iter(["a"])

    def input_once():
        try:
            return next(choices)
        except StopIteration:
            pytest.fail("Recorder prompt did not accept the accept choice.")

    monkeypatch.setattr("builtins.input", input_once)
    recorder.record(str(tmp_path / "recording.mp3"))


def test_recorder_service_generate(tmp_path, monkeypatch):
    class FakeRecorder:
        instances = []

        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.recorded = []
            self.triggered = False
            self.format = kwargs["format"]
            self.channels = kwargs["channels"]
            self.rate = kwargs["rate"]
            self.chunk = kwargs["chunk"]
            self.device_index = kwargs["device_index"]
            self.trim_silence_threshold = kwargs["trim_silence_threshold"]
            self.trim_buffer_start = kwargs["trim_buffer_start"]
            self.trim_buffer_end = kwargs["trim_buffer_end"]
            self.callback_delay = kwargs["callback_delay"]
            self.instances.append(self)

        def _trigger_set_device(self):
            self.triggered = True

        def record(self, path, message):
            self.recorded.append((path, message))

    init_calls = []
    msg_box_calls = []
    prompt_calls = []

    def initialize(service, kwargs, transcription_model=None):
        init_calls.append((dict(kwargs), transcription_model))
        service.cache_dir = kwargs.get("cache_dir", tmp_path)
        service.additional_kwargs = dict(kwargs)
        service.transcription_model = transcription_model

    monkeypatch.setattr("manim_voiceover.services.recorder.prompt_ask_missing_extras", lambda *args: prompt_calls.append(args))
    monkeypatch.setattr("manim_voiceover.services.recorder.Recorder", FakeRecorder)
    monkeypatch.setattr("manim_voiceover.services.recorder.initialize_speech_service", initialize)
    monkeypatch.setattr(
        "manim_voiceover.services.recorder.msg_box",
        lambda message: msg_box_calls.append(message) or f"boxed:{message}",
    )

    default_service = RecorderService(format=7, cache_dir=tmp_path)
    assert default_service.recorder.kwargs == {
        "format": 7,
        "channels": 1,
        "rate": 44100,
        "chunk": 512,
        "device_index": None,
        "trim_silence_threshold": -40.0,
        "trim_buffer_start": 200,
        "trim_buffer_end": 200,
        "callback_delay": 0.05,
    }

    service = RecorderService(
        format=8,
        channels=2,
        rate=22050,
        chunk=256,
        device_index=3,
        cache_dir=tmp_path,
        transcription_model="small",
        trim_silence_threshold=-35.5,
        trim_buffer_start=123,
        trim_buffer_end=456,
        callback_delay=0.25,
        global_speed=1.25,
        custom_option="kept",
    )
    assert service.recorder.kwargs == {
        "format": 8,
        "channels": 2,
        "rate": 22050,
        "chunk": 256,
        "device_index": 3,
        "trim_silence_threshold": -35.5,
        "trim_buffer_start": 123,
        "trim_buffer_end": 456,
        "callback_delay": 0.25,
    }
    assert init_calls == [
        ({"cache_dir": tmp_path}, "base"),
        ({"cache_dir": tmp_path, "global_speed": 1.25, "custom_option": "kept"}, "small"),
    ]
    assert prompt_calls == [
        (["pyaudio", "pynput"], "recorder", "RecorderService"),
        (["pyaudio", "pynput"], "recorder", "RecorderService"),
    ]

    with pytest.raises(ImportError) as exc_info:
        RecorderService(format=None, cache_dir=tmp_path)
    assert str(exc_info.value) == 'Missing packages. Run `pip install "manim-voiceover[recorder]"` to use RecorderService.'
    assert prompt_calls[-1] == (["pyaudio", "pynput"], "recorder", "RecorderService")

    cache_queries = []
    basename_inputs = []

    def get_cached_result(input_data, cache_dir):
        cache_queries.append((input_data, cache_dir))
        return None

    service.get_cached_result = get_cached_result
    service.get_audio_basename = lambda input_data: basename_inputs.append(input_data) or "generated-audio"

    cache_dir = tmp_path / "cache"
    result = service.generate_from_text("hello <bookmark mark='x'/>", cache_dir=cache_dir)
    expected_input_data = {
        "input_text": "hello ",
        "config": {
            "format": 8,
            "channels": 2,
            "rate": 22050,
            "chunk": 256,
        },
        "service": "recorder",
    }
    assert cache_queries == [(expected_input_data, cache_dir)]
    assert basename_inputs == [expected_input_data]
    assert msg_box_calls == ["Voiceover:\n\nhello "]
    assert service.recorder.triggered is True
    assert service.recorder.recorded == [
        (str(cache_dir / "generated-audio.mp3"), "boxed:Voiceover:\n\nhello "),
    ]
    assert result == {
        "input_text": "hello <bookmark mark='x'/>",
        "input_data": expected_input_data,
        "original_audio": "generated-audio.mp3",
    }

    cached = {
        "input_text": "cached",
        "input_data": expected_input_data,
        "original_audio": "cached.mp3",
    }
    service.get_cached_result = lambda input_data, cache_dir: cached
    assert service.generate_from_text("hello <bookmark mark='x'/>", cache_dir=cache_dir) is cached
