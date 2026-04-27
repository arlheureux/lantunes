import os
import shutil
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

def remove_missing_tracks(db, music_path):
    """Remove tracks from DB whose files no longer exist in the music library."""
    all_tracks = db.query(Track).all()
    deleted = 0
    deleted_albums = 0
    deleted_artists = 0
    
    print(f"Checking {len(all_tracks)} tracks for missing files...")
    
    # Track IDs to delete
    tracks_to_delete = []
    album_ids_to_check = set()
    artist_ids_to_check = set()
    
    for track in all_tracks:
        if not os.path.exists(track.path):
            tracks_to_delete.append(track.id)
            album_ids_to_check.add(track.album_id)
            artist_ids_to_check.add(track.artist_id)
            deleted += 1
    
    if deleted == 0:
        return 0
    
    # Delete missing tracks
    db.query(Track).filter(Track.id.in_(tracks_to_delete)).delete(synchronize_session=False)
    
    # Delete orphaned albums (no remaining tracks)
    for album_id in album_ids_to_check:
        remaining = db.query(Track).filter(Track.album_id == album_id).count()
        if remaining == 0:
            album = db.query(Album).get(album_id)
            if album:
                # Delete artwork file if it exists
                if album.artwork_path and os.path.exists(album.artwork_path):
                    try:
                        os.remove(album.artwork_path)
                    except Exception as e:
                        print(f"Error deleting artwork {album.artwork_path}: {e}")
                db.delete(album)
                deleted_albums += 1
    
    # Delete orphaned artists (no remaining tracks)
    for artist_id in artist_ids_to_check:
        remaining = db.query(Track).filter(Track.artist_id == artist_id).count()
        if remaining == 0:
            artist = db.query(Artist).get(artist_id)
            if artist:
                # Delete artwork file if it exists
                if artist.artwork_path and os.path.exists(artist.artwork_path):
                    try:
                        os.remove(artist.artwork_path)
                    except Exception as e:
                        print(f"Error deleting artist artwork {artist.artwork_path}: {e}")
                db.delete(artist)
                deleted_artists += 1
    
    db.commit()
    
    if deleted_albums > 0 or deleted_artists > 0:
        print(f"Cleanup: deleted {deleted_albums} orphaned albums, {deleted_artists} orphaned artists")
    
    return deleted


def rescan_unknown_tracks(db, total_files, scanned, progress_callback=None):
    """Rescan tracks with Unknown Artist or Unknown Album to update if metadata was fixed."""
    
    # Find tracks with Unknown Artist
    unknown_artist = db.query(Artist).filter(Artist.name == 'Unknown').first()
    
    # Find tracks with Unknown Album
    unknown_album = db.query(Album).filter(Album.title == 'Unknown Album').first()
    
    if not unknown_artist and not unknown_album:
        return 0
    
    # Get tracks that need rescanning
    tracks_to_rescan = []
    
    if unknown_artist:
        tracks = db.query(Track).filter(Track.artist_id == unknown_artist.id).all()
        tracks_to_rescan.extend(tracks)
    
    if unknown_album:
        tracks = db.query(Track).filter(Track.album_id == unknown_album.id).all()
        for t in tracks:
            if t not in tracks_to_rescan:
                tracks_to_rescan.append(t)
    
    total = len(tracks_to_rescan)
    if total == 0:
        return 0
    
    send_progress(f"Rescanning {total} tracks with unknown metadata...", current=scanned, total=total_files, stage="rescan")
    
    updated = 0
    for i, track in enumerate(tracks_to_rescan):
        if not os.path.exists(track.path):
            continue
        
        send_progress(f"Rescanning: {os.path.basename(track.path)}", current=scanned + i + 1, total=total_files, stage="rescan")
        
        try:
            meta = extract_metadata(track.path)
            
            new_artist_name = meta.get('artist')
            new_album_title = meta.get('album')
            
            artist_changed = False
            album_changed = False
            
            # Handle artist update
            if new_artist_name:
                real_artist = db.query(Artist).filter(Artist.name == new_artist_name).first()
                if not real_artist:
                    real_artist = Artist(name=new_artist_name)
                    db.add(real_artist)
                    db.flush()
                
                if track.artist_id != real_artist.id:
                    track.artist_id = real_artist.id
                    artist_changed = True
            
            # Handle album update
            if new_album_title:
                real_artist_for_album = db.query(Artist).get(track.artist_id) if track.artist_id != unknown_artist.id else None
                artist_id_for_album = real_artist_for_album.id if real_artist_for_album else None
                
                real_album = db.query(Album).filter(Album.title == new_album_title).first()
                if not real_album:
                    real_album = Album(
                        title=new_album_title,
                        artist_id=track.artist_id,
                        year=meta.get('year'),
                        genre=meta.get('genre')
                    )
                    db.add(real_album)
                    db.flush()
                    
                    # Try to fetch artwork for new album
                    artist_name_for_lookup = new_artist_name or (real_artist_for_album.name if real_artist_for_album else 'Unknown')
                    year_str = str(meta.get('year')) if meta.get('year') else None
                    
                    send_progress(f"Fetching artwork for {new_album_title}", current=scanned + i + 1, total=total_files, stage="artwork")
                    artwork_path = extract_and_save_artwork(track.path, real_album.id)
                    if not artwork_path:
                        artwork_path = fetch_album_cover(artist_name_for_lookup, new_album_title, real_album.id, year_str)
                    
                    if artwork_path:
                        real_album.artwork_path = artwork_path
                
                if track.album_id != real_album.id:
                    track.album_id = real_album.id
                    album_changed = True
            
            # Update track metadata
            if meta.get('title'):
                track.title = meta.get('title')
            if meta.get('year'):
                track.year = meta.get('year')
            if meta.get('disc'):
                track.disc_number = meta.get('disc')
            if meta.get('track'):
                track.track_number = meta.get('track')
            
            if artist_changed or album_changed or meta.get('title'):
                updated += 1
        
        except Exception as e:
            print(f"Error rescanning {track.path}: {e}")
    
    db.commit()
    
    # Cleanup orphaned Unknown entries (if no tracks reference them)
    if unknown_artist:
        remaining = db.query(Track).filter(Track.artist_id == unknown_artist.id).count()
        if remaining == 0:
            db.delete(unknown_artist)
    
    if unknown_album:
        remaining = db.query(Track).filter(Track.album_id == unknown_album.id).count()
        if remaining == 0:
            db.delete(unknown_album)
    
    db.commit()
    return updated


def scan_library(music_path: str, progress_callback=None):
    global _progress_callback
    original_callback = _progress_callback
    _progress_callback = progress_callback
    
    if not music_path or not os.path.isdir(music_path):
        return {"scanned": 0, "added": 0, "deleted": 0, "errors": 0}
    
    abs_path = os.path.abspath(music_path)
    if ".." in music_path or not abs_path.startswith("/"):
        return {"scanned": 0, "added": 0, "deleted": 0, "errors": 1, "error": "Invalid path"}
    
    db = SessionLocal()
    scanned = 0
    added = 0
    deleted = 0
    errors = 0
    skipped_format = 0
    skipped_duplicate = 0
    skipped_symlink = 0
    unsupported_formats = {}
    
    send_progress("Counting files...", stage="counting")
    total_files = 0
    for root, dirs, files in os.walk(music_path, followlinks=False):
        dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
        for filename in files:
            ext = Path(filename).suffix.lower()
            if ext in AUDIO_EXTENSIONS:
                total_files += 1
    
    send_progress(f"Found {total_files} audio files", current=0, total=total_files, stage="scanning")
    
    try:
        for root, dirs, files in os.walk(music_path, followlinks=False):
            dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
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
                    album = db.query(Album).filter(Album.title == album_title).first()
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
        
        # Remove tracks whose files no longer exist
        deleted = remove_missing_tracks(db, music_path)
        if deleted > 0:
            print(f"Removed {deleted} tracks that no longer exist")
        
        # Rescan tracks with Unknown Artist or Unknown Album
        rescan_updated = rescan_unknown_tracks(db, total_files, scanned)
        if rescan_updated > 0:
            print(f"Updated {rescan_updated} tracks with improved metadata")
        
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
    
    print(f"Scan complete: Scanned={scanned}, Added={added}, Deleted={deleted}, Errors={errors}, Skipped(duplicate)={skipped_duplicate}, Skipped(unsupported_format)={skipped_format}")
    if unsupported_formats:
        print(f"Unsupported formats found: {unsupported_formats}")
    
    return {"scanned": scanned, "added": added, "deleted": deleted, "errors": errors, "skipped_duplicate": skipped_duplicate, "skipped_format": skipped_format, "unsupported_formats": unsupported_formats}