from types import SimpleNamespace

import pytest
from manim_voiceover.services.recorder import RecorderService
from manim_voiceover.services.recorder.utility import MyListener, Recorder


class FakeAudio:
    def __init__(self):
        self.terminated = False

    def get_host_api_info_by_index(self, index):
        return {"deviceCount": 2}

    def get_device_info_by_host_api_device_index(self, host_api_index, device_index):
        return {"maxInputChannels": 2, "name": f"mic-{device_index}", "defaultSampleRate": 44100.0}

    def open(self, **kwargs):
        return FakeStream()

    def get_sample_size(self, format):
        return 2

    def terminate(self):
        self.terminated = True


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


def test_listener_tracks_record_key():
    listener = MyListener()
    listener.on_press(SimpleNamespace(char="r"))
    assert listener.key_pressed is True
    listener.on_release(SimpleNamespace(char="r"))
    assert listener.key_pressed is False

    listener.on_press(SimpleNamespace(r=True))
    assert listener.key_pressed is True
    listener.on_release(SimpleNamespace(shift_r=True))
    assert listener.key_pressed is False


def test_recorder_guard_helpers_raise():
    recorder = Recorder(channels=None, device_index=None)
    with pytest.raises(RuntimeError):
        recorder._listener()
    with pytest.raises(RuntimeError):
        recorder._scheduler()
    with pytest.raises(RuntimeError):
        recorder._channels()
    with pytest.raises(RuntimeError):
        recorder._stream()


def test_recorder_sets_device_from_input(monkeypatch):
    recorder = Recorder(channels=None, device_index=None)
    recorder.audio = FakeAudio()
    monkeypatch.setattr("builtins.input", lambda: "1")
    recorder._trigger_set_device()
    assert recorder.device_index == 1
    assert recorder.channels == 2
    assert recorder.rate == 44100


def test_recorder_device_error_paths(monkeypatch):
    recorder = Recorder(channels=None, device_index=0)
    recorder.audio = FakeAudio()
    recorder._trigger_set_device()
    assert recorder.channels == 2

    class BadAudio(FakeAudio):
        def get_host_api_info_by_index(self, index):
            return {"deviceCount": "two"}

    bad = Recorder()
    bad.audio = BadAudio()
    with pytest.raises(RuntimeError):
        bad._set_device()

    class MissingChannelsAudio(FakeAudio):
        def get_device_info_by_host_api_device_index(self, host_api_index, device_index):
            return {"maxInputChannels": "bad", "name": "mic", "defaultSampleRate": 44100.0}

    bad_channels = Recorder()
    bad_channels.audio = MissingChannelsAudio()
    with pytest.raises(RuntimeError):
        bad_channels._set_channels_from_device_index(0)

    class MissingRateAudio(FakeAudio):
        def get_device_info_by_host_api_device_index(self, host_api_index, device_index):
            return {"maxInputChannels": 1, "name": "mic", "defaultSampleRate": "fast"}

    bad_rate = Recorder()
    bad_rate.audio = MissingRateAudio()
    with pytest.raises(RuntimeError):
        bad_rate._set_rate_from_device_index(0)

    monkeypatch.setattr("builtins.input", lambda: (_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(SystemExit):
        recorder._set_device()


def test_recorder_record_sets_up_scheduler(monkeypatch, tmp_path):
    recorder = Recorder(channels=1, device_index=0, callback_delay=0.01)
    recorder.audio = FakeAudio()

    class FakeListener:
        def start(self):
            self.started = True

    class OneShotScheduler(FakeTask):
        def run(self):
            self.ran = True

    monkeypatch.setattr("manim_voiceover.services.recorder.utility.MyListener", FakeListener)
    monkeypatch.setattr(
        "manim_voiceover.services.recorder.utility.sched.scheduler", lambda time_fn, sleep_fn: OneShotScheduler()
    )
    recorder._record(str(tmp_path / "recording.mp3"))

    assert recorder.listener.started is True
    assert recorder.task.ran is True


def test_recorder_record_task_start_and_stop(monkeypatch, tmp_path):
    recorder = Recorder(channels=1, device_index=0, rate=10, chunk=1)
    recorder.audio = FakeAudio()
    recorder.listener = SimpleNamespace(key_pressed=True)
    recorder.task = FakeTask()
    recorder.frames = [b"a"] * 10
    fake_wave = FakeWave()
    exported = []

    monkeypatch.setattr("manim_voiceover.services.recorder.utility.wave.open", lambda path, mode: fake_wave)
    monkeypatch.setattr(
        "manim_voiceover.services.recorder.utility.trim_silence",
        lambda segment, **kwargs: SimpleNamespace(export=lambda path, format: exported.append((path, format))),
    )
    monkeypatch.setattr("manim_voiceover.services.recorder.utility.AudioSegment.from_wav", lambda path: object())
    monkeypatch.setattr("manim_voiceover.services.recorder.utility.wav2mp3", lambda path: exported.append(path))

    output_path = str(tmp_path / "recording.mp3")
    recorder._record_task(output_path)
    assert recorder.started is True
    assert recorder.task.entered

    recorder.listener.key_pressed = False
    recorder._record_task(output_path)
    assert recorder.started is False
    assert recorder.audio is None
    assert fake_wave.closed is True
    assert exported


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
    monkeypatch.setattr(recorder, "_record", lambda path: recorded.append(path))
    monkeypatch.setattr("builtins.input", iter(["l", "r", "a"]).__next__)
    monkeypatch.setattr("manim_voiceover.services.recorder.utility.AudioSegment.from_file", lambda path: "audio")
    monkeypatch.setattr("manim_voiceover.services.recorder.utility.play", lambda audio: played.append(audio))

    recorder.record(str(tmp_path / "recording.mp3"), message="say it")
    assert len(recorded) == 2
    assert played == ["audio"]


def test_recorder_record_invalid_and_keyboard_interrupt(monkeypatch, tmp_path):
    recorder = Recorder(channels=1, device_index=0)
    monkeypatch.setattr(recorder, "_record", lambda path: None)
    monkeypatch.setattr("builtins.input", iter(["x", "a"]).__next__)
    recorder.record(str(tmp_path / "recording.mp3"))

    monkeypatch.setattr("builtins.input", lambda: (_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(SystemExit):
        recorder.record(str(tmp_path / "recording.mp3"))


def test_recorder_service_generate(tmp_path, monkeypatch):
    class FakeRecorder:
        format = 1
        channels = 2
        rate = 44100
        chunk = 512

        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.recorded = []

        def _trigger_set_device(self):
            self.triggered = True

        def record(self, path, message):
            self.recorded.append((path, message))

    monkeypatch.setattr("manim_voiceover.services.recorder.prompt_ask_missing_extras", lambda *args: None)
    monkeypatch.setattr("manim_voiceover.services.recorder.Recorder", FakeRecorder)
    service = RecorderService(format=1, device_index=0, cache_dir=tmp_path, transcription_model=None)
    result = service.generate_from_text("hello <bookmark mark='x'/>", path="recorded.mp3")
    assert result["original_audio"] == "recorded.mp3"
    assert service.recorder.recorded[0][0].endswith("recorded.mp3")
