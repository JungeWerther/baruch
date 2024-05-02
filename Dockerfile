FROM python:3.11

# Install portaudio
RUN apt-get update && apt-get install -y libasound-dev libportaudio2 libportaudiocpp0 portaudio19-dev libsndfile1-dev alsa-utils pulseaudio git-lfs gcc python3-pyaudio \
&& rm -rf /var/lib/apt/lists/*

RUN usermod -a -G audio root

# The app directory is created in the container; persisted to ./src in the host
WORKDIR /src
COPY . /src

# Install the requirements
COPY ./requirements.txt ./
RUN pip install -r requirements.txt

# why?
# COPY . .
