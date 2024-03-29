from flask import Flask, redirect, request, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
import webbrowser
import threading

load_dotenv()

app = Flask(__name__, template_folder='templates')

# Credenciais da API e  Scopes
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = "http://localhost:8080/callback"
SCOPE = 'playlist-read-private playlist-modify-public user-library-modify user-library-read'

# Criação do cliente OAuth
sp_oauth = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPE)

# Route do Flask pra autorizar o usuário
@app.route('/authorize')
def authorize():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

# Route do Flask pra autorizar o callback
@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    access_token = token_info['access_token']

    # Criar um client do Spotify com o access_token
    sp = spotipy.Spotify(auth=access_token)

    # Ler as tracks salvas do usuário
    results = sp.current_user_saved_tracks()

    # Pegar a lista de músicas das Descobertas da Semana original
    discover_weekly = sp.user_playlist('spotify', '37i9dQZEVXcNaMmYylhqug')

    # Pegar a lista de músicas da playlist, se já criada anteriormente
    playlist_name = "Baú de descobertas"
    playlists = sp.user_playlists(sp.current_user()['id'])
    playlist_id = None
    for playlist in playlists['items']:
        if playlist['name'] == playlist_name:
            playlist_id = playlist['id']
            break

    if playlist_id is None:
        playlist_description = 'Guarda todas as descobertas da semana. Automatizado por oton1'
        playlist = sp.user_playlist_create(user=sp.current_user()['id'], name=playlist_name, public=True, description=playlist_description)
        playlist_id = playlist['id']

    playlist_tracks = sp.playlist_tracks(playlist_id)
    playlist_tracks_ids = [track['track']['id'] for track in playlist_tracks['items']]
    track_uris = []
    
    # Adicionar todas as músicas da playlist de Descobertas à playlist automatizada
    for track in discover_weekly['tracks']['items']:
        if track['track']['id'] not in playlist_tracks_ids:
            track_uris.append(track['track']['uri'])
    
    if track_uris:
        sp.playlist_add_items(playlist_id, track_uris)
    
    playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"

    return render_template('update_file.html', playlist_name=playlist_name, playlist_url = playlist_url)

# Flask route pro botão de criar a playlist
@app.route('/')

def index():
    return render_template('index.html')

def open_browser():
    webbrowser.open('http://127.0.0.1:8080/', new=1)

if __name__ == '__main__':
    threading.Timer(1, open_browser).start()
    app.run(port=8080, debug=True)
