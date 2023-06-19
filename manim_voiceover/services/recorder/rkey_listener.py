def has_keyboard_listener():
    try:
        from pynput import keyboard;
        import os
        if os.environ('MANIM_USE_PYNPUT', 'yes') in ['yes', 'true', '1']:
            return True
        else:
            return False
    except:
        return False

if has_keyboard_listener():
    # Keyboard listener is more powerful but requires some privileges that
    # could lead to a security issues.
    print('Using pynput.keyboard')
    from pynput import keyboard;
    class RKeyListener(keyboard.Listener):
        def __init__(self, verbose=False):
            super(RKeyListener, self).__init__(self.on_press, self.on_release)
            self.key_pressed = None
            self.verbose = verbose
        def on_press(self, key):
            if not hasattr(key, "char"):
                return True

            if key.char == "r":
                self.key_pressed = True
                if self.verbose:
                    print('R key pressed')
            return True

        def on_release(self, key):
            if not hasattr(key, "char"):
                return True

            if key.char == "r":
                self.key_pressed = False
                if self.verbose:
                    print('R key released')

            return True
else:
    print('Using readchar. If you want a system wide key listener, set environment variable MANIM_USE_PYNPUT=yes')
    import readchar, threading, time
    from collections import namedtuple
    PastKeyboardEvent = namedtuple('PastKeyboardEvent', ['key', 'time'])
    class KeyboardCapture(threading.Thread):
        instance = None
        @staticmethod
        def get_instance():
            return KeyboardCapture.instance or KeyboardCapture()
        
        def __init__(self, autostart=True):
            if KeyboardCapture.instance is None:
                KeyboardCapture.instance = self
            else:
                raise InterruptedError("One instance of key capture already initialized")
            super(KeyboardCapture, self).__init__()
            self.last_key = None
            self.last_time = time.time()
            self.capturing = False
            if autostart:
                self.start()
        def get_last_key(self):
            return PastKeyboardEvent(self.last_key, self.last_time)
            
        def run(self):
            self.capturing = True
            while self.capturing:
                self.last_key = readchar.readchar()
                self.last_time = time.time()
                if self.last_key == '\x03':
                    raise KeyboardInterrupt()
        def stop(self):
            self.capturing = False

    class RKeyListener(threading.Thread):

        def __init__(self, verbose=True):
            super(RKeyListener, self).__init__()
            # Delay for the first repetition
            self.first_repeat = 0.5
            # Delay for subsequent repetitions
            self.repeat_rate = 0.2
            self.key_pressed = False
            self.verbose = verbose
            
        def run(self):
            '''
            Relies on the fact that if you hold a key it will be 
            entered repeatedly on the therminal to detect the press and release
            events.
            '''
            self.keyboard = None
            try:
                self.keyboard = KeyboardCapture.get_instance()
                self.run_logic(self.keyboard)
            finally:
                if self.keyboard is not None:
                    self.keyboard.stop()

        def run_logic(self, keyboard):
            prev_time = keyboard.get_last_key().time
            first = False
            self.listening = True
            if self.verbose:
                print('Start listening')
            while self.listening:
                k =  keyboard.get_last_key()
                
                if not self.key_pressed:
                    if k.key in ('r', 'R') and k.time > prev_time:
                        self.key_pressed = True
                        if self.verbose:
                            print('R key pressed')
                        first = True
                        time.sleep(self.first_repeat - self.repeat_rate)
                else:
                    if k.key not in ('r', 'R') or k.time == prev_time:
                        if self.verbose:
                            print('R key released')
                        self.key_pressed = False
                prev_time = k.time
                time.sleep(self.repeat_rate)
            if self.verbose:
                print('Stop listening')
        def stop(self):
            self.keyboard.stop()
            self.listening = False
            self.join()
if __name__ == '__main__':
    RKeyListener(verbose=True)
