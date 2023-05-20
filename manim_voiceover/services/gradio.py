from queue import Queue
from manim import config
from manim_voiceover.services.base import SpeechService
from manim_voiceover.helper import prompt_ask_missing_extras
from subprocess import Popen, DEVNULL, PIPE
from pathlib import Path

class GradioRecordingService(SpeechService):
    ''' 
    The idea here is to show how to create create an asyncrhonous queue
    using a generator
    '''
    def __init__(self, filler_duration=False, inline=True, port=None, **kwargs):
        SpeechService.__init__(self, **kwargs)
        self._text_queue = None
        self._audio_queue = None
        self._interface = None
        self.use_filler = False
        self.inline = inline
        self.filler_duration = 1.0
        self.gradio_server_port = port
    
    
    def generate_from_text(
        self, text: str, cache_dir: str = None, path: str = None, duration=1, **kwargs
    ) -> dict:
        
        if cache_dir is None:
            cache_dir = self.cache_dir
        cache_path = Path(cache_dir)
        
        if self.use_filler or config.dry_run:
            input_data = {"input_text": text, "service": "gradio", "filler": True,"duration": duration or self.filler_duration}
            audio_path = f'quiet-{input_data["duration"]:.2f}.mp3'
            self.generate_silence(str(cache_path / audio_path), input_data['duration'])
        else:
            input_data = {"input_text": text, "service": "gradio"}
            if not config.disable_caching:
              cached_result = self.get_cached_result(input_data, cache_dir)
              if cached_result is not None and Path(cache_path / cached_result.get('original_audio', '')).is_file():
                  return cached_result

            if path is None:
                audio_path = self.get_data_hash(input_data) + ".mp3"
            else:
                audio_path = path
            self.record_if_needed(str(cache_path / audio_path), text)
        
        json_dict = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }
        return json_dict
    
    def generate_silence(self, fname, duration):
        result = Popen(f'ffmpeg -f lavfi -i anullsrc=channel_layout=mono:sample_rate=48000 -c:a mp3 -y -t {float(duration)}'.split() + [fname], 
                       stdout=DEVNULL, stderr=DEVNULL)
        if result.wait() != 0:
            raise RuntimeError('Unable to generate silent audio')
    

    def record_if_needed(self, fname, text):
        if Path(fname).is_file():
            return fname;
        
        tmp_file = self.prompt_recording(text)
        tmp_path = Path(tmp_file)
        if tmp_path.is_file():
            tmp_path.parent.mkdir(parents=True, exist_ok=True)
            result = Popen(['ffmpeg', '-i', tmp_file, '-vn', '-c:a', 'mp3', '-y', fname],
                       stdout=DEVNULL, stderr=PIPE)
            if result.wait() == 0:
                return
            else:
                raise RuntimeError(result.stderr.read().decode('utf-8'))
        else:
            raise RuntimeError('File recording failed to generate file')
    
    def prompt_recording(self, text):
        if self._text_queue is None:
            self._text_queue = Queue()
            self._audio_queue = Queue()
        self._text_queue.put(text)
        if self._interface is None:
            prompt_ask_missing_extras("gradio", "gradio", "GradioRecordingService")
            self.create_interface()
        return self._audio_queue.get()
    
    def create_interface(self):
        import gradio
        try:
            import IPython.display as ipd
        except ImportError:
            ipd = None
        with gradio.Blocks() as interface:
            def format_next_script_line():
                line = self._text_queue.get()
                if line is None:
                    raise StopIteration
                return f'<h2>speak the following line</h2><blockquote><h2>{line}</h2></blockquote>'
            prompt = gradio.HTML(format_next_script_line())
            with gradio.Row(visible=True) as recorder:
                audio_input = gradio.Audio(source='microphone', type='filepath')
            action_btn = gradio.Button('Accept', visible=False)
            
            def next_line(action, audio):
                self._audio_queue.put(audio)
                if action == 'Done':
                    interface.close()
                    return
                try:
                    return {prompt: format_next_script_line(), audio_input: None, 
                           action_btn: gradio.update(value='Accept', visible=False)}
                except StopIteration:
                    return {
                        prompt: "Recording finished",
                        action_btn: gradio.update(value='Done',visible=True),
                        recorder: gradio.update(visible=False)
                    }
            def audio_recorded(a):
                if a is None:
                    return {action_btn: gradio.update(value='Accept', visible=False)}
                else:
                    return {action_btn: gradio.update(value='Accept', visible=True)}
            audio_input.change(audio_recorded, [audio_input], [action_btn])
            action_btn.click(next_line, [action_btn, audio_input], [recorder, prompt, action_btn, audio_input])
        self._interface = interface
        
        if self.gradio_server_port is None:
            self._interface.launch(share=True, inline=self.inline, show_tips=True)
        else:
            self._interface.launch(inline=False, server_port=self.gradio_server_port)
            if self.inline and ipd is not None:
                ipd.HTML(
                f'''<div><iframe src="http://127.0.0.1:{self.gradio_server_port}/" width="{interface.width}" height="{interface.height}"
                allow="autoplay; camera; microphone; clipboard-read; clipboard-write;" frameborder="0" allowfullscreen>
                </iframe></div>'''
                )