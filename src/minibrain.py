from sock import Socket
import wave
import ssl
from faster_whisper import WhisperModel
from time import time
from prompt import yield_stream
from owntongue import Voice
import threading
import subprocess
from queue import Queue
import re
import os

password = os.getenv("PASSWORD").encode()
model_size = "tiny.en"
FILENAME = "instruction.wav"
END_RESPONSE_FILENAME = "./wavs/my_lord.wav"
    
print("[LOADING MODELS]", flush=True)
MODEL = WhisperModel(model_size, device="cpu", compute_type="int8")
VOICE = Voice()
print("[DONE]", flush=True)

# def number_to_word(match):
#     num_dict = {1: 'firstly,', 2: 'secondly,', 3: 'thirdly,', 4: 'fourthly,', 5: 'fifthly,',
#                 6: 'sixthly,', 7: 'seventhly,', 8: 'eighthly,', 9: 'ninthly,', 10: 'tenthly,'}
#     return num_dict[int(match.group(0)[:-1])]

def chunk_to_sentence(word_stream):
    acc = ''
    delim = ['.', ':', ';', '?', '!']
    for word in word_stream:
        word = re.sub(r'\d+\.', '', word)
        acc += word

        # this just gets recognized often
        replace_list = [
            "Go grace.", 
            "the grace.", 
            "For Grace,",
            "So Grace,"
            ]
        
        for phrase in replace_list:
            if phrase in acc:
                acc = acc.replace(phrase, "")

        for token in delim:
            if token in acc:
                yield acc
                acc = ''
                break

def concatenate_segments(iterator):
    string = ""
    for segment in iterator:
        print(segment.text)
        string += segment.text if segment.text != "Why not?" else ""
    return string

def speak(filename):
    subprocess.call(["aplay", filename])
    
    # OPTIONAL: delete the file after playing it.
    # subprocess.call(["rm", filename])

def speaker(speech_queue: Queue):
    while True:
        filename = speech_queue.get()
        if filename is None:
            break
        speak(filename)

def synthesiser(brain_queue: Queue, speech_queue: Queue):
    while True:
        sentence = brain_queue.get()
        if sentence is None:
            speech_queue.put(None)
            break
        filename = VOICE.from_self(sentence)
        speech_queue.put(filename)

def generator(queue: Queue, speech_segments):
    for sentence in chunk_to_sentence(yield_stream(speech_segments)):
        print(sentence, end='', flush=True)
        queue.put(sentence)
    queue.put(None)
    print("[PRODUCER][DONE]")

def transcribe_file():
    brain_queue = Queue()
    speech_queue = Queue()

    # transcribe it.
    print("[TRANSCRIBING]")
    start_time = time()
    segments, info = MODEL.transcribe(FILENAME, beam_size=5)
    speech_segments = concatenate_segments(segments)
    print("[TRANSCRIBED IN]", time() - start_time, "seconds")
    
    # loop over the returned sentences
    # in multi-threaded execution.
    speech_consumer = threading.Thread(target=speaker, args=(speech_queue,))
    speech_consumer.start()

    consumer = threading.Thread(target=synthesiser, args=(brain_queue, speech_queue,))
    consumer.start()

    producer = threading.Thread(target=generator, args=(brain_queue, speech_segments,))
    producer.start()
    
    producer.join()
    consumer.join()
    speech_consumer.join()
        
def write_buffer_to_file(buffer):
    with wave.open(FILENAME, 'wb') as file: 
        file.setnchannels(1)
        file.setsampwidth(2)  # 2 bytes for 16-bit audio
        file.setframerate(16000)  # Standard sample rate
        file.writeframes(buffer)

def handle_sock_file_reception(buffer):
    with Socket(ports=(8866, 8867), host="127.0.0.1") as sock:
        sock.send(password)
        print('[READY]', flush=True)
        while True:
            try:
                data = sock.recv(1024)
                if not data:
                    return
                if data == b'[STOP]':
                    sock.send(b'[MINIBRAIN][RECEIVED]')
                yield data
                
            except Exception as e:
                raise Exception(e)

def client():
   
    buffer = b''
    half_window = 20480

    while True:
        try:
            for data in handle_sock_file_reception(buffer):
                match data:    
                    case b'[START]':
                        print('received [START]', flush=True)
                        buffer = b''
                    
                    case b'[STOP]':
                        print('received [STOP]', flush=True)

                        if len(buffer) > half_window:

                            write_buffer_to_file(buffer)
                            buffer = b''
                            transcribe_file()
                            subprocess.call(["aplay", END_RESPONSE_FILENAME])
                    
                    case bytes():
                        buffer += data

        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    client()
# class Prompt():
#     def __init__(self, input)

    