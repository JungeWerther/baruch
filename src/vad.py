import pyaudio
import numpy as np
from openwakeword.model import Model
# import torch
import json
import time
import subprocess
import io
import websockets
import asyncio

import datetime

# connections variable for websocket

class Listener():
    def __init__(self):
        self.listening = False
        self.threshold = 0.007
        self.ticks = 0
        self.max_ticks = 50
        self.in_data = None
        self.prediction = None
        self.p = pyaudio.PyAudio()
        self.ws = None
        self.CONNECTIONS = set()

        self.load_model()
        self.initialize_listener()
        self.run_stream()

    async def main(self):
        async with websockets.serve(self.register, "baruch.local", 8765):
            await self.responder()
    
    def __exit__(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    async def register(self, websocket):
        self.CONNECTIONS.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.CONNECTIONS.remove(websocket)

    async def responder(self):
        print("executing")
        while True:
            await self.run_stream()

    def load_model(self):
        self.model = Model(
            wakeword_models=["./models/djuu_seppuh.tflite"],
            vad_threshold = 0.1
            )

    def listen(self):
        self.ticks = -50
        self.handleListen()

    def antiping(self):
        if self.listening:
            if -100 < self.ticks < 0:
                self.ticks -= 1
            else:
                self.ticks = 0 
            
    def ping(self):
        if self.listening:
            self.ticks += 1
            if self.ticks > self.max_ticks:
                self.handleStopListen()
            
    def handleListen(self):
        if not self.listening:
            self.listening = True
            print("starting to listen", self.listening)
            websockets.broadcast(self.CONNECTIONS, "[START]")

            if len(self.CONNECTIONS) > 0:
                self.play('hey')
            else:
                self.play('connect_brain')

    def handleStopListen(self):
        if self.listening:
            self.listening = False
            print("not listening anymore", self.listening)
            websockets.broadcast(self.CONNECTIONS, "[STOP]")

    def play(self, name):
        """default options: 'connect_brain', 'hey', 'seb'
        """
        subprocess.call(["aplay", f"../wavs/{name}.wav"])

    def callback(self, in_data, frame_count, time_info, status):
        self.in_data = in_data
        return in_data, pyaudio.paContinue
    
    async def run_stream(self):
        if self.stream.is_active():            
            if self.in_data is not None:
                self.process_chunk(self.in_data)

                if not self.listening:
                    await asyncio.sleep(0.05)
                else:
                    websockets.broadcast(self.CONNECTIONS, self.in_data)


    def initialize_listener(self):
        # audio recording defaults

        CHUNK = 1024
        RATE = 16000
        device_index = 1


        self.stream = self.p.open(
            input_device_index = device_index,
            format=pyaudio.paInt16, 
            channels=1, 
            rate=RATE, 
            input=True, 
            frames_per_buffer=CHUNK,
            stream_callback=self.callback
            )

        self.stream.start_stream()

    def process_chunk(self, frame):
        chunk_i16 = np.frombuffer(frame, dtype=np.int16)
        
        self.prediction = self.model.predict(chunk_i16)["djuu_seppuh"]

        if self.prediction > self.threshold:
            self.listen()
        
        if self.listening:
            if self.prediction == 0:
                self.ping()
            else:
                print(self.ticks)
                self.antiping()

async def init_session():
    while True:
        websockets.broadcast(listener.CONNECTIONS, "here")
        await asyncio.sleep(2)

if __name__ == "__main__":
    listener = Listener()
    asyncio.run(listener.main())