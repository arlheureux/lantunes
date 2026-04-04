import os
from mutagen import File as MutagenFile
from pathlib import Path
from database import SessionLocal, Artist, Album, Track
from metadata import extract_metadata

AUDIO_EXTENSIONS = {'.flac', '.mp3', '.m4a', '.ogg', '.wav', '.aac', '.wma'}

def scan_library(music_path: str):
    if not music_path or not os.path.isdir(music_path):
        return {"scanned": 0, "added": 0, "errors": 0}
    
    db = SessionLocal()
    scanned = 0
    added = 0
    errors = 0
    
    try:
        for root, dirs, files in os.walk(music_path):
            for filename in files:
                ext = Path(filename).suffix.lower()
                if ext not in AUDIO_EXTENSIONS:
                    continue
                
                scanned += 1
                filepath = os.path.join(root, filename)
                
                existing = db.query(Track).filter(Track.path == filepath).first()
                if existing:
                    continue
                
                try:
                    meta = extract_metadata(filepath)
                    
                    artist = db.query(Artist).filter(Artist.name == (meta.get('artist') or 'Unknown')).first()
                    if not artist:
                        artist = Artist(name=meta.get('artist') or 'Unknown')
                        db.add(artist)
                        db.flush()
                    
                    album_title = meta.get('album') or 'Unknown Album'
                    album = db.query(Album).filter(Album.title == album_title, Album.artist_id == artist.id).first()
                    if not album:
                        album = Album(
                            title=album_title,
                            artist_id=artist.id,
                            year=meta.get('year'),
                            genre=meta.get('genre')
                        )
                        db.add(album)
                        db.flush()
                    
                    track = Track(
                        title=meta.get('title', Path(filename).stem),
                        album_id=album.id,
                        artist_id=artist.id,
                        disc_number=meta.get('disc', 1),
                        track_number=meta.get('track'),
                        duration=meta.get('duration'),
                        path=filepath,
                        file_format=ext[1:].upper(),
                        bitrate=meta.get('bitrate'),
                        sample_rate=meta.get('sample_rate')
                    )
                    db.add(track)
                    added += 1
                    
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
                    errors += 1
        
        db.commit()
    except Exception as e:
        db.rollback()
        errors += 1
    finally:
        db.close()
    
    return {"scanned": scanned, "added": added, "errors": errors}