try:
    from pynput import keyboard
    class RKeyListener(keyboard.Listener):
        def __init__(self, verbose=False):
            super(MyListener, self).__init__(self.on_press, self.on_release)
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
except ImportError:
    import readchar, threading, time
    from collections import namedtuple
    PastKeyboardEvent = namedtuple('PastKeyboardEvent', ['key', 'time'])
    class KeyboardCapture(threading.Thread):
        instance = None
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

    class RKeyListener(threading.Thread):

        def __init__(self, verbose=False):
            super(RKeyListener, self).__init__()
            # Delay for the first repetition
            self.first_repeat = 0.5
            # Delay for subsequent repetitions
            self.repeat_rate = 0.2
            self.key_pressed = False
            self.verbose = verbose
            self.start()
            
        def run(self):
            '''
            Relies on the fact that if you hold a key it will be 
            entered repeatedly on the therminal to detect the press and release
            events.
            '''
            try:
                keyboard = KeyboardCapture()
                self.run_logic(keyboard)
            finally:
                keyboard.capturing = False

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
        def stop_listening(self):
            self.listening = False;
if __name__ == '__main__':
    RKeyListener(verbose=True)