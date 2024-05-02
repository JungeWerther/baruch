#!/bin/bash

cd ../whisper.cpp

./main -m models/ggml-tiny.en.bin -f ../wavs/stream.wav -oj -of ../wavs/stream