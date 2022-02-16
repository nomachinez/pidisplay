# Run this from the same directory you run PiDisplay from 

import datetime
import hashlib
import os

from spotipy import SpotifyPKCE, CacheFileHandler

redirect_uri = "http://localhost:8888/callback"
scope = "user-read-playback-state,user-modify-playback-state"
state = hashlib.sha256()
state.update(str.encode(str(datetime.datetime.now().timestamp() * 1000)))
state = state.hexdigest()
client_id = input("Enter your client id (from Spotify): ")
username = input("Enter your Spotify username: ")

handler = CacheFileHandler(cache_path=os.path.join(os.getcwd(), ".cache-{}".format(username)), username=username)
credential_manager = SpotifyPKCE(scope=scope, open_browser=False, client_id=client_id,
                                 state=state, redirect_uri=redirect_uri, cache_handler=handler)

token = credential_manager.get_access_token()
print(token)
del token


