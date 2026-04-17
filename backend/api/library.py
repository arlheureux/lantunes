import sys
import os
import json
import asyncio
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.responses import StreamingResponse
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from database import get_db, Track, Album, Artist
from scanner import scan_library, set_progress_callback
from dependencies import require_admin, get_current_user
from models import User

import config as config_module

router = APIRouter(prefix="/api/library", tags=["library"])

config = config_module.config

@router.get("/tracks")
def get_tracks(db: Session = Depends(get_db), page: int = 1, limit: int = 50):
    offset = (page - 1) * limit
    tracks = db.query(Track).order_by(Track.title).offset(offset).limit(limit).all()
    total = db.query(Track).count()
    return {"tracks": [t.as_dict() for t in tracks], "total": total, "page": page, "limit": limit}

@router.get("/tracks/{track_id}")
def get_track(track_id: int, db: Session = Depends(get_db)):
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track.as_dict()

@router.post("/tracks/batch")
def get_tracks_batch(ids: list[int], db: Session = Depends(get_db)):
    """Get multiple tracks by their IDs in a single request."""
    if not ids:
        return {}
    if len(ids) > 500:
        ids = ids[:500]  # Limit to 500 tracks per request
    tracks = db.query(Track).filter(Track.id.in_(ids)).all()
    return {t.id: t.as_dict() for t in tracks}

@router.get("/albums")
def get_albums(db: Session = Depends(get_db)):
    """Get all albums."""
    albums = db.query(Album).options(joinedload(Album.artist)).order_by(Album.title).all()
    return [{"id": a.id, "title": a.title, "artist": a.artist.name if a.artist else "Unknown", "year": a.year, "artwork": a.artwork_path} for a in albums]

@router.get("/albums/recent")
def get_recent_albums(db: Session = Depends(get_db), limit: int = 8):
    """Get recently added albums."""
    albums = db.query(Album).options(joinedload(Album.artist)).order_by(Album.created_at.desc()).limit(limit).all()
    return [{"id": a.id, "title": a.title, "artist": a.artist.name if a.artist else "Unknown", "year": a.year, "artwork": a.artwork_path, "created_at": a.created_at.isoformat() if a.created_at else None} for a in albums]

@router.get("/genres")
def get_genres(db: Session = Depends(get_db)):
    """Get list of all genres in the library."""
    genres = db.query(Album.genre).distinct().filter(Album.genre != None).order_by(Album.genre).all()
    return [g[0] for g in genres if g[0]]

@router.get("/genres/{genre}")
def get_albums_by_genre(genre: str, db: Session = Depends(get_db)):
    """Get albums by genre."""
    albums = db.query(Album).options(joinedload(Album.artist)).filter(Album.genre == genre).order_by(Album.title).all()
    return [{"id": a.id, "title": a.title, "artist": a.artist.name if a.artist else "Unknown", "year": a.year, "artwork": a.artwork_path} for a in albums]

@router.get("/albums/{album_id}")
def get_album(album_id: int, db: Session = Depends(get_db)):
    album = db.query(Album).options(joinedload(Album.artist), joinedload(Album.tracks)).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    return {
        "id": album.id,
        "title": album.title,
        "artist": album.artist.name if album.artist else "Unknown",
        "artist_id": album.artist_id,
        "year": album.year,
        "genre": album.genre,
        "artwork": album.artwork_path,
        "tracks": [t.as_dict() for t in sorted(album.tracks, key=lambda x: (x.disc_number or 1, x.track_number or 0))]
    }

@router.put("/albums/{album_id}")
def update_album(album_id: int, title: str = None, year: int = None, genre: str = None, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    if title is not None: album.title = title
    if year is not None: album.year = year
    if genre is not None: album.genre = genre
    db.commit()
    return {"id": album.id, "title": album.title, "year": album.year, "genre": album.genre, "artwork": album.artwork_path}

@router.delete("/albums/{album_id}/artwork")
def remove_album_artwork(album_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    if album.artwork_path:
        album.artwork_path = None
        db.commit()
    return {"success": True}

@router.get("/artists")
def get_artists(db: Session = Depends(get_db)):
    artists = db.query(Artist).order_by(Artist.name).all()
    return [{"id": a.id, "name": a.name, "artwork": a.artwork_path} for a in artists]

@router.get("/artists/{artist_id}")
def get_artist(artist_id: int, db: Session = Depends(get_db)):
    artist = db.query(Artist).options(joinedload(Artist.albums)).filter(Artist.id == artist_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    return {
        "id": artist.id,
        "name": artist.name,
        "artwork": artist.artwork_path,
        "albums": [{"id": a.id, "title": a.title, "year": a.year, "artwork": a.artwork_path} for a in artist.albums]
    }

@router.get("/search")
def search(q: str = Query(...), db: Session = Depends(get_db)):
    q_lower = f"%{q.lower()}%"
    
    # Search tracks by title or artist name
    tracks = db.query(Track).join(Artist).filter(
        (Track.title.ilike(q_lower)) | (Artist.name.ilike(q_lower))
    ).limit(50).all()
    
    # Search albums by title or artist name
    albums = db.query(Album).join(Artist).filter(
        (Album.title.ilike(q_lower)) | (Artist.name.ilike(q_lower))
    ).limit(30).all()
    
    # Search artists by name
    artists = db.query(Artist).filter(Artist.name.ilike(q_lower)).limit(30).all()
    
    return {
        "tracks": [t.as_dict() for t in tracks],
        "albums": [{"id": a.id, "title": a.title, "artist": a.artist.name if a.artist else "Unknown", "year": a.year, "artwork": a.artwork_path} for a in albums],
        "artists": [{"id": a.id, "name": a.name, "artwork": a.artwork_path} for a in artists]
    }

@router.post("/scan")
async def trigger_scan(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    music_path = config.get("library", {}).get("music_path", "")
    if not music_path:
        raise HTTPException(status_code=400, detail="Music path not configured")
    if not os.path.isdir(music_path):
        raise HTTPException(status_code=400, detail="Music path does not exist")
    
    # Run scan in a thread to not block the event loop
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as executor:
        result = await asyncio.get_event_loop().run_in_executor(
            executor, scan_library, music_path, None
        )
    return result

@router.get("/scan/stream")
async def scan_stream():
    """SSE endpoint for scan progress"""
    import concurrent.futures
    
    music_path = config.get("library", {}).get("music_path", "")
    if not music_path:
        return StreamingResponse(
            iter([f"data: {json.dumps({'error': 'Music path not configured'})}\n\n"]),
            media_type="text/event-stream"
        )
    
    async def event_generator():
        progress_data = {"current": 0, "total": 0, "message": "Starting...", "stage": "preparing", "percent": 0}
        
        def progress_callback(data):
            progress_data.update(data)
        
        def run_scan():
            from scanner import scan_library as _scan
            return _scan(music_path, progress_callback)
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_scan)
            
            # Keep sending progress while scan is running
            while not future.done():
                if progress_data.get("message"):
                    yield f"data: {json.dumps(progress_data)}\n\n"
                await asyncio.sleep(0.5)
            
            # Send final result
            result = future.result()
            final_data = {
                "current": progress_data.get("total", 0),
                "total": progress_data.get("total", 0),
                "message": f"Scan complete! Added {result.get('added', 0)} tracks",
                "stage": "complete",
                "percent": 100,
                "result": result
            }
            yield f"data: {json.dumps(final_data)}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/artwork/{album_id}")
def get_artwork(album_id: int, db: Session = Depends(get_db)):
    from fastapi.responses import FileResponse
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album or not album.artwork_path:
        raise HTTPException(status_code=404, detail="Artwork not found")
    if not os.path.exists(album.artwork_path):
        raise HTTPException(status_code=404, detail="Artwork file not found")
    return FileResponse(album.artwork_path, media_type="image/jpeg")

@router.post("/fetch-covers")
def fetch_missing_covers(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """Fetch covers for albums that don't have artwork yet"""
    from metadata import fetch_album_cover
    
    albums_without_art = db.query(Album).options(joinedload(Album.artist)).filter(Album.artwork_path == None).all()
    fetched = 0
    
    for album in albums_without_art:
        if album.artist:
            year_str = str(album.year) if album.year else None
            artwork_path = fetch_album_cover(album.artist.name, album.title, album.id, year_str)
            if artwork_path:
                album.artwork_path = artwork_path
                fetched += 1
    
    db.commit()
    return {"fetched": fetched, "total_without_artwork": len(albums_without_art)}

@router.get("/artwork/artist/{artist_id}")
def get_artist_artwork(artist_id: int, db: Session = Depends(get_db)):
    from fastapi.responses import FileResponse
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if not artist or not artist.artwork_path:
        raise HTTPException(status_code=404, detail="Artist artwork not found")
    if not os.path.exists(artist.artwork_path):
        raise HTTPException(status_code=404, detail="Artist artwork file not found")
    return FileResponse(artist.artwork_path, media_type="image/jpeg")

@router.post("/fetch-artist-images")
def fetch_missing_artist_images(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """Fetch images for artists that don't have artwork yet"""
    from metadata import fetch_artist_image
    
    artists_without_art = db.query(Artist).filter(Artist.artwork_path == None).all()
    fetched = 0
    
    for artist in artists_without_art:
        artwork_path = fetch_artist_image(artist.name, artist.id)
        if artwork_path:
            artist.artwork_path = artwork_path
            fetched += 1
    
    db.commit()
    return {"fetched": fetched, "total_without_artwork": len(artists_without_art)}

@router.get("/fetch-artwork/stream")
async def fetch_artwork_stream(current_user: User = Depends(require_admin)):
    """SSE endpoint for fetching missing artwork (album covers + artist images)"""
    import concurrent.futures
    from metadata import fetch_album_cover, fetch_artist_image
    
    async def event_generator():
        progress_data = {"current": 0, "total": 0, "message": "Starting...", "stage": "preparing", "percent": 0}
        
        def send_progress(msg, current, total, stage):
            progress_data.update({
                "message": msg,
                "current": current,
                "total": total,
                "stage": stage,
                "percent": round((current / total * 100), 1) if total > 0 else 0
            })
        
        def run_fetch():
            from database import SessionLocal
            db = SessionLocal()
            albums_fetched = 0
            artists_fetched = 0
            
            try:
                albums = db.query(Album).options(joinedload(Album.artist)).filter(Album.artwork_path == None).all()
                total_albums = len(albums)
                
                if total_albums > 0:
                    send_progress(f"Fetching album covers ({total_albums} albums)", 0, total_albums, "album_covers")
                    
                    for i, album in enumerate(albums):
                        send_progress(f"Fetching: {album.title}", i + 1, total_albums, "album_covers")
                        if album.artist:
                            year_str = str(album.year) if album.year else None
                            artwork_path = fetch_album_cover(album.artist.name, album.title, album.id, year_str)
                            if artwork_path:
                                album.artwork_path = artwork_path
                                albums_fetched += 1
                    
                    db.commit()
                
                # Fetch artist images
                artists = db.query(Artist).filter(Artist.artwork_path == None).all()
                total_artists = len(artists)
                
                if total_artists > 0:
                    send_progress(f"Fetching artist images ({total_artists} artists)", 0, total_artists, "artist_images")
                    
                    for i, artist in enumerate(artists):
                        send_progress(f"Fetching: {artist.name}", i + 1, total_artists, "artist_images")
                        artwork_path = fetch_artist_image(artist.name, artist.id)
                        if artwork_path:
                            artist.artwork_path = artwork_path
                            artists_fetched += 1
                    
                    db.commit()
                
                return {"albums_fetched": albums_fetched, "artists_fetched": artists_fetched}
                
            except Exception as e:
                return {"error": str(e), "albums_fetched": albums_fetched, "artists_fetched": artists_fetched}
            finally:
                db.close()
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_fetch)
            
            while not future.done():
                if progress_data.get("message"):
                    yield f"data: {json.dumps(progress_data)}\n\n"
                await asyncio.sleep(0.3)
            
            result = future.result()
            final_data = {
                "current": progress_data.get("total", 0),
                "total": progress_data.get("total", 0),
                "message": f"Complete! Fetched {result.get('albums_fetched', 0)} album covers, {result.get('artists_fetched', 0)} artist images",
                "stage": "complete",
                "percent": 100,
                "result": result
            }
            yield f"data: {json.dumps(final_data)}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")