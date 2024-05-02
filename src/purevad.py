import pyaudio
import ssl
import os
import queue
from time import time
import numpy as np
import subprocess
from dotenv import load_dotenv

from openwakeword.model import Model
from sock import Server

# LOL
password = os.getenv("PASSWORD")

GREETING_FILENAME = "./wavs/yeah.wav"
END_FILENAME = "./wavs/okay.wav"

class Stream():
    def __init__(self):
        self.buffer = queue.Queue()
        self.stop_iteration = False

    def __enter__(self):
        CHUNK = 1024
        RATE = 16000
        device_index = 1

        self.p = pyaudio.PyAudio()

        self.stream = self.p.open(
            input_device_index = device_index,
            format=pyaudio.paInt16, 
            channels=1, 
            rate=RATE, 
            input=True, 
            frames_per_buffer=CHUNK,
            stream_callback=self._callback
            )

        self.stream.start_stream()

        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        self.stop_iteration = True
    
    def __iter__(self):
        return self
    
    def __next__(self):
        try:
            chunk = self.buffer.get(block=True, timeout=1)    
            return chunk
        except queue.Empty:
            print("Giuseppe: queue empty.")
            raise StopIteration   

    def _callback(self, data_in, frame_count, time_info, status):
        self.buffer.put(data_in)
        return data_in, pyaudio.paContinue
    
class Controller():
    def __init__(self):
        self.mode = "[MUSIC]"
        self.muted = False
    
    def greet(self):
        subprocess.run(["aplay", GREETING_FILENAME])

    def end_greeting(self):
        subprocess.run(["aplay", END_FILENAME])

    def mute(self):
        subprocess.call("amixer -D pulse sset Master mute".split())

    def lower_volume(self):
        subprocess.call("amixer -D pulse sset Master 50%-".split())
    
    def unmute(self):
        subprocess.call("amixer -D pulse sset Master unmute".split())

    def higher_volume(self):
        subprocess.call("amixer -D pulse sset Master 50%+".split())

    def handle_start_listening(self):
        self.greet()
        if self.mode == "[MUSIC]":
            self.lower_volume()
        elif self.mode == "[FILM]":
            self.mute()
        return True
    
    def handle_stop_listening(self):
        if self.mode == "[MUSIC]":
            self.higher_volume()
        elif self.mode == "[FILM]":
            self.unmute()

class Vad():
    """Class for running VAD detection"""
    def __init__(self, vad_threshold=0.3, ww_threshold=0.05, attention_span=2):
        self.controller = Controller()
        self.model = Model(
            wakeword_models=["./models/djuu_seppuh.tflite"],
            vad_threshold = vad_threshold
            )
        
        self.ww_threshold = ww_threshold
        self.attention_span = attention_span

        self.start_time = None
        self.listening = False
    
    def handle_start_listening(self):
        if self.controller.handle_start_listening():
            self.listening = True
            self.start_time = time()
            return '[START]'

    def handle_stop_listening(self):
        self.controller.handle_stop_listening()
        self.listening = False
        elapsed_time = time() - self.start_time
        print('[ELAPSED TIME]', elapsed_time, 'seconds')
        return '[STOP]'
    
    def check_start(self, prediction: float):
        if not self.listening:
            if prediction > self.ww_threshold: 
                return self.handle_start_listening()
    
    def check_stop(self, avg: float):
        if self.listening:
            if avg < 0.0001:
                return self.handle_stop_listening()
    
    def activate(self, stream):

        predictions = []
        
        for frame in stream:
            pred = vad.predict(frame)
            yield self.check_start(pred)

            # calculate average of last predictions. If 0, it has been silent long enough.
            predictions.append(pred)
            if len(predictions) > 40:
                avg = np.mean(predictions[-30:])
                predictions.pop(0) 
                yield self.check_stop(avg)

            if self.listening:
                yield frame
            
            # self.attention_span - elapsed_time is a nice metric for UX
    def disable_volume(self):
        if self.mode == "[MUSIC]":
            self.lower_volume()
        elif self.mode == "[FILM]":
            self.mute()
    
    def enable_volume(self):
        if self.mode == "[MUSIC]":
            self.higher_volume()
        elif self.mode == "[FILM]":
            self.unmute()

    def check_elapsed_time(self):
        return time() - self.start_time if self.start_time is not None else None
    
    def predict(self, frame):
        chunk = np.frombuffer(frame, dtype=np.int16)
        pred = self.model.predict(chunk)["djuu_seppuh"]
        return pred
    
    def mute(self):
        os.system("amixer -D pulse sset Master mute")

    def unmute(self):
        os.system("amixer -D pulse sset Master unmute")

    def lower_volume(self):
        os.system("amixer -D pulse sset Master 50%-")

    def higher_volume(self):
        os.system("amixer -D pulse sset Master 50%+")

if __name__ == "__main__":
    vad = Vad()
    print('[IMPORTED ALL]', flush=True)
    serv = Server("0.0.0.0", ports=(8866, 8867))
    print('[INITIALIZED SERVER SOCKET]', flush=True)
    with serv as s:
        s.listen()
        while True:
            try:
                print("waiting for connection...", flush=True)
                conn, addr = s.accept()
                print(f"socket connected to {addr}")
            
                # first packet after connection should be password
                check = conn.recv(1024)
                
                if check == password:
                    print('[IDENTIFIED]')
                else:
                    print('[WRONG PASSWORD]')
                    conn.close
                    continue

                with Stream() as stream:
                    for frame in vad.activate(stream):
                        match frame:
                            case '[START]':
                                conn.send(frame.encode())
                            
                            case '[STOP]':
                                conn.send(frame.encode())
                                ans = conn.recv(1024)
                                vad.controller.end_greeting()
                                print(ans)
                                conn.close()
                                break
                            
                            case bytes():
                                conn.send(frame)
            
            except KeyboardInterrupt:                 
                print("[EXITING]")
                break
            except:
                print("[ERROR] Connection failed")
                continue