import subprocess
import threading
from time import time

class Voice():
    def __init__(self, filename=None):
        self.filename = filename or "./wavs/" + str(time()) + ".wav"

    def from_self(self, text):
        
        command1 = ['echo', text]
        command2 = ['piper', '--model', 'en_GB-alan-low.onnx', '--output_file', self.filename]

        process1 = subprocess.Popen(command1, stdout=subprocess.PIPE)
        process2 = subprocess.Popen(command2, stdin=process1.stdout, stdout=subprocess.PIPE)

        process1.stdout.close()  # Allow process1 to receive a SIGPIPE if process2 exits.
        output, _ = process2.communicate()

        # Speak in a different thread.
        return self.filename
        # print("[READY TO SAY]", text, flush=True)
        # threading.Thread(target=self.speak, args=(self.filename,)).start()

if __name__ == "__main__":
    text = 'Welcome, I am Giuseppe!'
    v = Voice("./wavs/okay.wav")
    v.from_self("I see")