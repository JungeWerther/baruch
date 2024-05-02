from purevad import Vad, Stream
from faster_whisper import WhisperModel, decode_audio

model_size = "tiny.en"

# Run on GPU with FP16

# or run on GPU with INT8
# model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
# or run on CPU with INT8
# model = WhisperModel(model_size, device="cpu", compute_type="int8")

if __name__ == "__main__":
    vad = Vad()
    model = WhisperModel(model_size, device="cpu")

    buffer = []
    listening = False

    with Stream() as stream:
        while True:
            print("[LISTENING]")
            for frame in vad.activate(stream):
                match frame:
                    case '[START]':
                        print('[START]')
                        listening=True
                    case '[STOP]':
                        print('[STOP]')
                        listening=False
                        break
                    case bytes():
                        if listening:
                            buffer.append(frame)
            
            segments, info = model.transcribe("welcome.wav", beam_size=5)

            print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

            for segment in segments:
                print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))