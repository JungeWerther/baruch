from purevad import Stream
from openwakeword.model import Model as Openwakeword
import numpy as np
from sock import Socket
# from minibrain import Brain
import time
import wave
import subprocess
import json

params = {
    "wakeword_threshold": 0.05,
    "wakeword_models": ["./models/djuu_seppuh.tflite"],
    "vad_threshold": 0.1,
    "attention_span": 3
}

class Model(Openwakeword):
    def __init__(self, attention_span, wakeword_threshold, listening=True, **kwargs):
        super().__init__(**kwargs)
        self.stream = Stream()
        self.threshold = wakeword_threshold
        self.stop_listening = False if listening else True
        self.last_awakened = self.set_last_awakened()
        self.attention_span = attention_span
        self.max_attention_span = attention_span
        self.stop_iteration = True
        self.finished = False
        self.first = True

    def set_last_awakened(self):
        self.last_awakened = time.time()
        return self.last_awakened
    
    def schedule_awake(self):
        self.last_awakened = time.time() + 1
    
    def process(self):
        with self.stream as stream:
            for chunk in stream:
                chunk_i16 = np.frombuffer(chunk, dtype=np.int16)

                if not self.stop_listening:
                    self.prediction = self.predict(chunk_i16)["djuu_seppuh"]

                    # if the wake word is being detected
                    if self.prediction > self.threshold:

                        # not sure if necessary anymore
                        if self.finished or self.first:

                            if self.get_elapsed_time() > self.attention_span + 0.5:
                                self.first = False

                                self.set_last_awakened()

                                stream_snippet = self.listen(stream)

                                self.create_wav(stream_snippet)
                                self.transcribe_current()
                                self.broadcast()
                                # self.set_last_awakened()
                                self.set_last_awakened()

                                self.finished = True
                                self.stop_listening = True
                else:
                    self.stop_listening = False

    def broadcast(self):
        with open("../wavs/stream.json") as obj:
            content = obj.read()
            output = json.loads(content)["transcription"][0]["text"]
            if output == " [BLANK_AUDIO]":
                print("I didn't hear you well")
            else:
                self.parse(output)

    def parse(self, output):
        # PromptObj(output)
        pass

    def transcribe_current(self):
        subprocess.call("./call_whisper.sh")
    
    def create_wav(self, snippet):
        with wave.open("../wavs/stream.wav", "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 2 bytes = 16 bits
            wav_file.setframerate(16000)  # 16 kHz
            for chunk in snippet:
                wav_file.writeframes(chunk)
            print("done writing")

    def open_socket(self):
        with Socket() as sock:
            for chunk in sock:
                print(chunk)

    def listen(self, stream):
        print("starting to listen...")
        if self.stop_listening:
            print("Denied. stop_listening is True")
            self.attention_span = self.max_attention_span
            
        else:
            # for chunk in self.parallel_stream():
            #     print(chunk)
            print("Listening...")
            for chunk in stream:
            #     print(self.get_elapsed_time())
            #     yield(chunk)
                
                if self.get_elapsed_time() > self.attention_span:
                    print("Exceeded attention_span")
                    # self.set_last_awakened()
                    break
                else:
                    # self.set_last_awakened()
                    # print(self.get_elapsed_time())
                    yield(chunk)
                    pass
    
    def get_elapsed_time(self):        
        elapsed_time = time.time() - self.last_awakened
        return elapsed_time

    def check_tired(self):
        if self.attention_span > 0:
            return True
        else:
            return False
            

model = Model(**params)
model.process()