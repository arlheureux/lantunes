import os
from mutagen import File as MutagenFile
from pathlib import Path
from database import SessionLocal, Artist, Album, Track
from metadata import extract_metadata, extract_and_save_artwork, fetch_album_cover

AUDIO_EXTENSIONS = {'.flac', '.mp3', '.m4a', '.ogg', '.wav', '.aac', '.wma', 
                   '.opus', '.ape', '.alac', '.aiff', '.aif', '.m4b', '.mpc', '.mp+'}

def scan_library(music_path: str):
    if not music_path or not os.path.isdir(music_path):
        return {"scanned": 0, "added": 0, "errors": 0}
    
    db = SessionLocal()
    scanned = 0
    added = 0
    errors = 0
    skipped_format = 0
    skipped_duplicate = 0
    unsupported_formats = {}
    
    try:
        for root, dirs, files in os.walk(music_path):
            for filename in files:
                ext = Path(filename).suffix.lower()
                if ext not in AUDIO_EXTENSIONS:
                    skipped_format += 1
                    unsupported_formats[ext] = unsupported_formats.get(ext, 0) + 1
                    continue
                
                scanned += 1
                filepath = os.path.join(root, filename)
                
                existing = db.query(Track).filter(Track.path == filepath).first()
                if existing:
                    skipped_duplicate += 1
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
                    artwork_path = None
                    
                    # Get artist name for cover lookup
                    artist_name = meta.get('artist') or 'Unknown'
                    
                    if not album:
                        album = Album(
                            title=album_title,
                            artist_id=artist.id,
                            year=meta.get('year'),
                            genre=meta.get('genre')
                        )
                        db.add(album)
                        db.flush()
                        
                        # Try to get artwork - first try embedded, then external providers
                        artwork_path = extract_and_save_artwork(filepath, album.id)
                        if not artwork_path:
                            # Try external providers
                            year_str = str(meta.get('year')) if meta.get('year') else None
                            artwork_path = fetch_album_cover(artist_name, album_title, album.id, year_str)
                        
                        if artwork_path:
                            album.artwork_path = artwork_path
                            db.commit()
                    elif not album.artwork_path:
                        # Album exists but no artwork - try external providers
                        year_str = str(album.year) if album.year else None
                        artwork_path = fetch_album_cover(artist_name, album_title, album.id, year_str)
                        if artwork_path:
                            album.artwork_path = artwork_path
                            db.commit()
                    
                    track = Track(
                        title=meta.get('title') or Path(filename).stem,
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
    
    print(f"Scan complete: Scanned={scanned}, Added={added}, Errors={errors}, Skipped(duplicate)={skipped_duplicate}, Skipped(unsupported_format)={skipped_format}")
    if unsupported_formats:
        print(f"Unsupported formats found: {unsupported_formats}")
    
    return {"scanned": scanned, "added": added, "errors": errors, "skipped_duplicate": skipped_duplicate, "skipped_format": skipped_format, "unsupported_formats": unsupported_formats}