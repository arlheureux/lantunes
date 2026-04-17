#!/usr/bin/env python3
"""Fix artwork for albums that have missing artwork but have files in the music folder."""

import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from database import SessionLocal, Album, Track

COMMON_ARTWORK_NAMES = [
    'cover.jpg', 'cover.jpeg', 'cover.png',
    'folder.jpg', 'folder.jpeg', 'folder.png',
    'album.jpg', 'album.jpeg', 'album.png',
    'front.jpg', 'front.jpeg', 'front.png',
    'thumb.jpg', 'thumb.jpeg', 'thumb.png',
    '.folder.jpg', '.folder.jpeg', '.folder.png',
    'coverart.jpg', 'coverart.jpeg', 'coverart.png',
]

def fix_missing_artwork():
    db = SessionLocal()
    fixed = 0
    not_found = 0
    
    try:
        # Get all albums without artwork
        albums_without_art = db.query(Album).filter(Album.artwork_path == None).all()
        total = len(albums_without_art)
        
        print(f"Found {total} albums without artwork")
        
        for i, album in enumerate(albums_without_art):
            # Find a track from this album
            track = db.query(Track).filter(Track.album_id == album.id).first()
            if not track or not track.path:
                not_found += 1
                continue
            
            audio_dir = os.path.dirname(track.path)
            
            # Check for common artwork filenames
            found = False
            for name in COMMON_ARTWORK_NAMES:
                art_path = os.path.join(audio_dir, name)
                if os.path.exists(art_path) and os.path.isfile(art_path):
                    # Copy to artwork directory
                    dest_path = os.path.join(backend_dir, 'artwork', f"album_{album.id}.jpg")
                    try:
                        import shutil
                        shutil.copy2(art_path, dest_path)
                        album.artwork_path = dest_path
                        db.commit()
                        print(f"  [{i+1}/{total}] Fixed: {album.title}")
                        fixed += 1
                        found = True
                        break
                    except Exception as e:
                        print(f"  Error copying {art_path}: {e}")
            
            if not found:
                not_found += 1
            
            if (i + 1) % 100 == 0:
                print(f"Progress: {i+1}/{total}")
        
        print(f"\nDone! Fixed: {fixed}, Not found: {not_found}")
    
    finally:
        db.close()


if __name__ == "__main__":
    fix_missing_artwork()
