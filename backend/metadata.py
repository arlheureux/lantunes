from mutagen import File

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
        'artwork': None
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
            
            for key in ['cover', 'Cover', 'APIC', 'METADATA_BLOCK_PICTURE']:
                if key in tags:
                    meta['artwork'] = key
                    break
        
        if hasattr(audio.info, 'length'):
            meta['duration'] = int(audio.info.length)
        if hasattr(audio.info, 'bitrate') and audio.info.bitrate:
            meta['bitrate'] = int(audio.info.bitrate // 1000)
        if hasattr(audio.info, 'sample_rate') and audio.info.sample_rate:
            meta['sample_rate'] = int(audio.info.sample_rate)
            
    except Exception as e:
        print(f"Error extracting metadata from {filepath}: {e}")
    
    return meta