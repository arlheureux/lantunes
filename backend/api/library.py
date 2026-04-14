import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from database import get_db, Track, Album, Artist, Playlist, PlaylistTrack, Client
from scanner import scan_library

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
def get_albums(db: Session = Depends(get_db), page: int = 1, limit: int = 50):
    """Get albums with optional pagination."""
    offset = (page - 1) * limit
    albums = db.query(Album).options(joinedload(Album.artist)).order_by(Album.title).offset(offset).limit(limit).all()
    total = db.query(Album).count()
    return {"albums": [{"id": a.id, "title": a.title, "artist": a.artist.name if a.artist else "Unknown", "year": a.year, "artwork": a.artwork_path} for a in albums], "total": total, "page": page, "limit": limit}

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
def update_album(album_id: int, title: str = None, year: int = None, genre: str = None, db: Session = Depends(get_db)):
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    if title is not None: album.title = title
    if year is not None: album.year = year
    if genre is not None: album.genre = genre
    db.commit()
    return {"id": album.id, "title": album.title, "year": album.year, "genre": album.genre, "artwork": album.artwork_path}

@router.delete("/albums/{album_id}/artwork")
def remove_album_artwork(album_id: int, db: Session = Depends(get_db)):
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
def trigger_scan(db: Session = Depends(get_db)):
    music_path = config.get("library", {}).get("music_path", "")
    if not music_path:
        raise HTTPException(status_code=400, detail="Music path not configured")
    if not os.path.isdir(music_path):
        raise HTTPException(status_code=400, detail="Music path does not exist")
    result = scan_library(music_path)
    return result

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
def fetch_missing_covers(db: Session = Depends(get_db)):
    """Fetch covers for albums that don't have artwork yet"""
    from metadata import fetch_album_cover
    
    albums_without_art = db.query(Album).filter(Album.artwork_path == None).all()
    fetched = 0
    
    for album in albums_without_art:
        artist = db.query(Artist).filter(Artist.id == album.artist_id).first()
        if artist:
            year_str = str(album.year) if album.year else None
            artwork_path = fetch_album_cover(artist.name, album.title, album.id, year_str)
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
def fetch_missing_artist_images(db: Session = Depends(get_db)):
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