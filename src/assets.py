from dagster import asset
from purevad import Vad, Stream
from sock import Socket, Server
import requests

@asset
def vad_stream():
    s = Stream()
    with s as stream:
        yield stream
                    
@asset
def repository():
    repo = requests.get("")
    with open("./data/repo", "w") as f:
        f.write(repo.json())

# @asset
# def dagster_integration():
#     repo = Repository()

