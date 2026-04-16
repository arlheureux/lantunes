#!/usr/bin/env python3
"""
Cleanup script to merge duplicate albums.
Keeps the album with the most tracks, moves all tracks to it, then deletes duplicates.
"""

import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from database import SessionLocal, Album, Track, Artist
from sqlalchemy import func


def cleanup_duplicate_albums():
    db = SessionLocal()
    
    try:
        print("Finding duplicate albums...")
        
        # Get albums with their track counts using a join and group by
        results = db.query(
            Album.id,
            Album.title,
            func.count(Track.id).label('track_count')
        ).outerjoin(Track, Album.id == Track.album_id).group_by(Album.id).all()
        
        # Group by title
        albums_by_title = {}
        for album_id, title, track_count in results:
            if title not in albums_by_title:
                albums_by_title[title] = []
            albums_by_title[title].append({'id': album_id, 'track_count': track_count})
        
        # Find titles with duplicates
        duplicates = {title: albums for title, albums in albums_by_title.items() if len(albums) > 1}
        
        if not duplicates:
            print("No duplicate albums found!")
            return
        
        print(f"Found {len(duplicates)} album titles with duplicates")
        
        total_merged = 0
        total_deleted = 0
        
        for title, album_list in duplicates.items():
            # Sort by track count (descending), then by id (ascending for tie-breaker)
            album_list.sort(key=lambda x: (-x['track_count'], x['id']))
            
            keep_album = album_list[0]
            duplicate_albums = album_list[1:]
            
            print(f"\nAlbum: '{title}'")
            print(f"  Keeping album {keep_album['id']} with {keep_album['track_count']} tracks")
            
            for dup in duplicate_albums:
                # Move tracks to keep album
                tracks_moved = db.query(Track).filter(Track.album_id == dup['id']).update(
                    {Track.album_id: keep_album['id']}
                )
                print(f"  Moved {tracks_moved} tracks from album {dup['id']}")
                total_merged += tracks_moved
                
                # Delete duplicate album
                album_to_delete = db.query(Album).filter(Album.id == dup['id']).first()
                if album_to_delete:
                    db.delete(album_to_delete)
                    print(f"  Deleted duplicate album {dup['id']}")
                    total_deleted += 1
        
        db.commit()
        
        # Clean up orphaned artists (artists with no albums)
        print("\nCleaning up orphaned artists...")
        orphaned = db.query(Artist).outerjoin(Album, Artist.id == Album.artist_id).filter(Album.id == None).all()
        for artist in orphaned:
            print(f"  Deleting orphaned artist: {artist.name} (id: {artist.id})")
            db.delete(artist)
        
        db.commit()
        
        print(f"\n=== Summary ===")
        print(f"Albums deleted: {total_deleted}")
        print(f"Tracks moved: {total_merged}")
        print("Done!")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    cleanup_duplicate_albums()
