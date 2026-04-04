import os
import base64
from mutagen import File
from pathlib import Path

ARTWORK_DIR = Path(__file__).parent.parent / "artwork"

def get_artwork_path(album_id: int) -> Path:
    ARTWORK_DIR.mkdir(exist_ok=True)
    return ARTWORK_DIR / f"album_{album_id}.jpg"

def extract_and_save_artwork(filepath: str, album_id: int) -> str | None:
    try:
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
                    import struct
                    pic_bytes = base64.b64decode(pic_data)
                    artwork_data = pic_bytes
                except Exception as e:
                    print(f"Error extracting FLAC artwork: {e}")
            
            # MP3 - uses APIC
            if not artwork_data and 'APIC' in tags:
                try:
                    apic = tags['APIC'][0]
                    if hasattr(apic, 'data'):
                        artwork_data = apic.data
                except Exception as e:
                    print(f"Error extracting MP3 artwork: {e}")
        
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