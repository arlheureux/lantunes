import os
from mutagen import File as MutagenFile
from pathlib import Path
from database import SessionLocal, Artist, Album, Track
from metadata import extract_metadata, extract_and_save_artwork, fetch_album_cover, fetch_artist_image

AUDIO_EXTENSIONS = {'.flac', '.mp3', '.m4a', '.ogg', '.wav', '.aac', '.wma', 
                   '.opus', '.ape', '.alac', '.aiff', '.aif', '.m4b', '.mpc', '.mp+'}

# Global progress callback for SSE
_progress_callback = None

def set_progress_callback(callback):
    global _progress_callback
    _progress_callback = callback

def send_progress(message, current=0, total=0, stage=""):
    if _progress_callback:
        _progress_callback({
            "message": message,
            "current": current,
            "total": total,
            "stage": stage,
            "percent": round((current / total * 100), 1) if total > 0 else 0
        })

def scan_library(music_path: str, progress_callback=None):
    global _progress_callback
    original_callback = _progress_callback
    _progress_callback = progress_callback
    
    if not music_path or not os.path.isdir(music_path):
        return {"scanned": 0, "added": 0, "errors": 0}
    
    # Path traversal prevention
    abs_path = os.path.abspath(music_path)
    if ".." in music_path or not abs_path.startswith("/"):
        return {"scanned": 0, "added": 0, "errors": 1, "error": "Invalid path"}
    
    db = SessionLocal()
    scanned = 0
    added = 0
    errors = 0
    skipped_format = 0
    skipped_duplicate = 0
    unsupported_formats = {}
    
    # Count total files first
    send_progress("Counting files...", stage="counting")
    total_files = 0
    for root, dirs, files in os.walk(music_path):
        for filename in files:
            ext = Path(filename).suffix.lower()
            if ext in AUDIO_EXTENSIONS:
                total_files += 1
    
    send_progress(f"Found {total_files} audio files", current=0, total=total_files, stage="scanning")
    
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
                
                send_progress(f"Processing: {filename}", current=scanned, total=total_files, stage="scanning")
                
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
                        send_progress(f"Extracting artwork for {album_title}", current=scanned, total=total_files, stage="artwork")
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
        
        # Fetch missing artist images
        artists_without_art = db.query(Artist).filter(Artist.artwork_path == None).all()
        total_artists = len(artists_without_art)
        if total_artists > 0:
            send_progress(f"Fetching artist images ({total_artists} artists)", current=0, total=total_artists, stage="artist_images")
            for i, artist in enumerate(artists_without_art):
                send_progress(f"Fetching: {artist.name}", current=i+1, total=total_artists, stage="artist_images")
                try:
                    artwork_path = fetch_artist_image(artist.name, artist.id)
                    if artwork_path:
                        artist.artwork_path = artwork_path
                except Exception as e:
                    print(f"Error fetching artist image for {artist.name}: {e}")
            db.commit()
        
        _progress_callback = original_callback
        send_progress("Scan complete!", current=total_files, total=total_files, stage="complete")
    except Exception as e:
        _progress_callback = original_callback
        send_progress(f"Error: {str(e)}", stage="error")
    finally:
        db.close()
    
    print(f"Scan complete: Scanned={scanned}, Added={added}, Errors={errors}, Skipped(duplicate)={skipped_duplicate}, Skipped(unsupported_format)={skipped_format}")
    if unsupported_formats:
        print(f"Unsupported formats found: {unsupported_formats}")
    
    return {"scanned": scanned, "added": added, "errors": errors, "skipped_duplicate": skipped_duplicate, "skipped_format": skipped_format, "unsupported_formats": unsupported_formats}