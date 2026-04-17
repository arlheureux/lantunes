import os
import sys
import time
import requests
from pathlib import Path
from typing import Optional

backend_dir = Path(__file__).parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))
from backend.config import config

ARTWORK_DIR = project_root / "artwork"

_last_musicbrainz_request = 0
_MUSICBRAINZ_MIN_INTERVAL = 1.1


def _rate_limit_musicbrainz():
    global _last_musicbrainz_request
    elapsed = time.time() - _last_musicbrainz_request
    if elapsed < _MUSICBRAINZ_MIN_INTERVAL:
        time.sleep(_MUSICBRAINZ_MIN_INTERVAL - elapsed)
    _last_musicbrainz_request = time.time()

def get_artwork_path(album_id: int) -> Path:
    ARTWORK_DIR.mkdir(exist_ok=True)
    return ARTWORK_DIR / f"album_{album_id}.jpg"

def get_artist_artwork_path(artist_id: int) -> Path:
    ARTWORK_DIR.mkdir(exist_ok=True)
    return ARTWORK_DIR / f"artist_{artist_id}.jpg"

def fetch_cover_from_musicbrainz(artist: str, album: str, year: str = None) -> Optional[bytes]:
    """Fetch cover from MusicBrainz/Cover Art Archive"""
    try:
        _rate_limit_musicbrainz()
        
        search_url = "https://musicbrainz.org/ws/2/release/"
        params = {
            'query': f'release:"{album}" AND artist:"{artist}"',
            'fmt': 'json',
            'limit': 1
        }
        
        headers = {'User-Agent': 'LanTunes/1.0 (contact@example.com)'}
        
        resp = requests.get(search_url, params=params, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        releases = data.get('releases', [])
        if not releases:
            return None
        
        release_id = releases[0]['id']
        
        # Get cover art from Cover Art Archive
        cover_url = f"https://coverartarchive.org/release/{release_id}/front"
        cover_resp = requests.get(cover_url, timeout=10, allow_redirects=True)
        
        if cover_resp.status_code == 200:
            return cover_resp.content
    
    except Exception as e:
        print(f"MusicBrainz lookup failed: {e}")
    
    return None

def fetch_cover_from_deezer(artist: str, album: str) -> Optional[bytes]:
    """Fetch cover from Deezer API"""
    try:
        # Search Deezer
        search_url = "https://api.deezer.com/search"
        params = {
            'q': f'{artist} {album}',
            'limit': 1
        }
        
        resp = requests.get(search_url, params=params, timeout=10)
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        tracks = data.get('data', [])
        if not tracks:
            return None
        
        # Get album cover from track
        album_id = tracks[0].get('album', {}).get('id')
        if not album_id:
            return None
        
        # Get album details for better cover
        album_url = f"https://api.deezer.com/album/{album_id}"
        album_resp = requests.get(album_url, timeout=10)
        
        if album_resp.status_code == 200:
            album_data = album_resp.json()
            cover_url = album_data.get('cover_xl') or album_data.get('cover_big') or album_data.get('cover')
            if cover_url:
                cover_resp = requests.get(cover_url, timeout=10)
                if cover_resp.status_code == 200:
                    return cover_resp.content
    
    except Exception as e:
        print(f"Deezer lookup failed: {e}")
    
    return None

def fetch_cover_from_lastfm(artist: str, album: str, api_key: str) -> Optional[bytes]:
    """Fetch cover from LastFM API"""
    if not api_key:
        return None
    
    try:
        search_url = "https://ws.audioscrobbler.com/2.0/"
        params = {
            'method': 'album.search',
            'album': album,
            'artist': artist,
            'api_key': api_key,
            'format': 'json',
            'limit': 5
        }
        
        resp = requests.get(search_url, params=params, timeout=10)
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        albums = data.get('results', {}).get('albums', {}).get('album', [])
        if not albums:
            return None
        
        # Get the first match's image
        for album_data in albums:
            images = album_data.get('image', [])
            for img in images:
                if img.get('size') in ['extralarge', 'large', 'medium']:
                    if img.get('#text'):
                        img_resp = requests.get(img['#text'], timeout=10)
                        if img_resp.status_code == 200:
                            return img_resp.content
        
        # Try largest image if no preferred size found
        if images and images[-1].get('#text'):
            img_resp = requests.get(images[-1]['#text'], timeout=10)
            if img_resp.status_code == 200:
                return img_resp.content
    
    except Exception as e:
        print(f"LastFM lookup failed: {e}")
    
    return None

def fetch_album_cover(artist: str, album: str, album_id: int, year: str = None) -> Optional[str]:
    """Try multiple providers to fetch album cover"""
    lastfm_config = config.get('lastfm', {})
    lastfm_api_key = lastfm_config.get('api_key') if lastfm_config else None
    
    providers = []
    
    # Add LastFM if API key is configured (try first)
    if lastfm_api_key:
        providers.append(lambda: fetch_cover_from_lastfm(artist, album, lastfm_api_key))
    
    # Add Deezer (fallback)
    providers.append(lambda: fetch_cover_from_deezer(artist, album))
    
    for provider in providers:
        try:
            artwork_data = provider()
            if artwork_data:
                art_path = get_artwork_path(album_id)
                with open(art_path, 'wb') as f:
                    f.write(artwork_data)
                return str(art_path)
        except Exception as e:
            print(f"Provider failed: {e}")
            continue
    
    return None

def extract_and_save_artwork(filepath: str, album_id: int) -> Optional[str]:
    """Extract embedded artwork or fetch from external provider"""
    import base64
    
    try:
        from mutagen import File
        audio = File(filepath)
        if audio is None:
            return None
        
        artwork_data = None
        
        if hasattr(audio, 'tags') and audio.tags:
            tags = audio.tags
            
            # FLAC/OGG - uses METADATA_BLOCK_PICTURE
            if 'METADATA_BLOCK_PICTURE' in tags:
                try:
                    pic_data = tags['METADATA_BLOCK_PICTURE'][0]
                    if hasattr(pic_data, 'value'):
                        pic_data = pic_data.value
                    pic_bytes = base64.b64decode(pic_data)
                    artwork_data = pic_bytes
                except Exception as e:
                    pass
            
            # MP3 - uses APIC
            if not artwork_data and 'APIC' in tags:
                try:
                    apic = tags['APIC'][0]
                    if hasattr(apic, 'data'):
                        artwork_data = apic.data
                except Exception as e:
                    pass
        
        if artwork_data:
            art_path = get_artwork_path(album_id)
            with open(art_path, 'wb') as f:
                f.write(artwork_data)
            return str(art_path)
    
    except Exception as e:
        print(f"Error extracting artwork from {filepath}: {e}")
    
    return None

def extract_metadata(filepath: str) -> dict:
    meta = {
        'title': None,
        'artist': None,
        'album': None,
        'year': None,
        'genre': None,
        'track': None,
        'disc': 1,
        'duration': None,
        'bitrate': None,
        'sample_rate': None,
    }
    
    try:
        from mutagen import File
        audio = File(filepath)
        if audio is None:
            return meta
        
        if hasattr(audio, 'tags') and audio.tags:
            tags = audio.tags
            
            if 'title' in tags:
                meta['title'] = str(tags['title'][0])
            if 'artist' in tags:
                meta['artist'] = str(tags['artist'][0])
            if 'album' in tags:
                meta['album'] = str(tags['album'][0])
            if 'date' in tags:
                try:
                    meta['year'] = int(str(tags['date'][0])[:4])
                except:
                    pass
            if 'genre' in tags:
                meta['genre'] = str(tags['genre'][0])
            if 'tracknumber' in tags:
                try:
                    meta['track'] = int(str(tags['tracknumber'][0]).split('/')[0])
                except:
                    pass
            if 'discnumber' in tags:
                try:
                    meta['disc'] = int(str(tags['discnumber'][0]).split('/')[0])
                except:
                    pass
        
        if hasattr(audio.info, 'length'):
            meta['duration'] = int(audio.info.length)
        if hasattr(audio.info, 'bitrate') and audio.info.bitrate:
            meta['bitrate'] = int(audio.info.bitrate // 1000)
        if hasattr(audio.info, 'sample_rate') and audio.info.sample_rate:
            meta['sample_rate'] = int(audio.info.sample_rate)
            
    except Exception as e:
        print(f"Error extracting metadata from {filepath}: {e}")
    
    return meta

def fetch_artist_image(artist_name: str, artist_id: int) -> Optional[str]:
    """Fetch artist image from external providers"""
    lastfm_config = config.get('lastfm', {})
    lastfm_api_key = lastfm_config.get('api_key') if lastfm_config else None
    
    providers = []
    
    if lastfm_api_key:
        providers.append(lambda: fetch_artist_from_lastfm(artist_name, lastfm_api_key))
    
    providers.append(lambda: fetch_artist_from_deezer(artist_name))
    
    for provider in providers:
        try:
            artwork_data = provider()
            if artwork_data:
                art_path = get_artist_artwork_path(artist_id)
                with open(art_path, 'wb') as f:
                    f.write(artwork_data)
                return str(art_path)
        except Exception as e:
            print(f"Artist image provider failed: {e}")
            continue
    
    return None

def fetch_artist_from_deezer(artist_name: str) -> Optional[bytes]:
    """Fetch artist image from Deezer API"""
    try:
        search_url = "https://api.deezer.com/search/artist"
        params = {'q': artist_name, 'limit': 1}
        
        resp = requests.get(search_url, params=params, timeout=10)
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        artists = data.get('data', [])
        if not artists:
            return None
        
        picture_url = artists[0].get('picture_xl') or artists[0].get('picture_big') or artists[0].get('picture')
        if not picture_url:
            return None
        
        img_resp = requests.get(picture_url, timeout=10)
        if img_resp.status_code == 200:
            return img_resp.content
    
    except Exception as e:
        print(f"Deezer artist lookup failed: {e}")
    
    return None

def fetch_artist_from_lastfm(artist_name: str, api_key: str) -> Optional[bytes]:
    """Fetch artist image from LastFM API"""
    try:
        search_url = "https://ws.audioscrobbler.com/2.0/"
        params = {
            'method': 'artist.search',
            'artist': artist_name,
            'api_key': api_key,
            'format': 'json',
            'limit': 1
        }
        
        resp = requests.get(search_url, params=params, timeout=10)
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        artists = data.get('results', {}).get('artistmatches', {}).get('artist', [])
        if not artists:
            return None
        
        mbid = artists[0].get('mbid')
        if not mbid:
            return None
        
        info_url = "https://ws.audioscrobbler.com/2.0/"
        info_params = {
            'method': 'artist.getInfo',
            'mbid': mbid,
            'api_key': api_key,
            'format': 'json'
        }
        
        info_resp = requests.get(info_url, params=info_params, timeout=10)
        if info_resp.status_code != 200:
            return None
        
        info_data = info_resp.json()
        images = info_data.get('artist', {}).get('image', [])
        
        for img in images:
            if img.get('size') in ['extralarge', 'large', 'medium']:
                url = img.get('#text')
                if url:
                    img_resp = requests.get(url, timeout=10)
                    if img_resp.status_code == 200:
                        return img_resp.content
    
    except Exception as e:
        print(f"LastFM artist lookup failed: {e}")
    
    return None