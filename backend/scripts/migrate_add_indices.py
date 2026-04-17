#!/usr/bin/env python3
"""Migration script to add indices and fix cascade deletes.

Run this script once to update the existing database schema.
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "lantunes.db")

def migrate():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Starting migration...")
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Add index on albums.artist_id if not exists
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_albums_artist_id ON albums(artist_id)")
        print("  Created index: ix_albums_artist_id")
    except sqlite3.OperationalError as e:
        print(f"  Index ix_albums_artist_id: {e}")
    
    # Add index on tracks.album_id if not exists
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_tracks_album_id ON tracks(album_id)")
        print("  Created index: ix_tracks_album_id")
    except sqlite3.OperationalError as e:
        print(f"  Index ix_tracks_album_id: {e}")
    
    # Add index on tracks.artist_id if not exists
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_tracks_artist_id ON tracks(artist_id)")
        print("  Created index: ix_tracks_artist_id")
    except sqlite3.OperationalError as e:
        print(f"  Index ix_tracks_artist_id: {e}")
    
    # Add index on playlists.user_id if not exists
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_playlists_user_id ON playlists(user_id)")
        print("  Created index: ix_playlists_user_id")
    except sqlite3.OperationalError as e:
        print(f"  Index ix_playlists_user_id: {e}")
    
    # Add index on playlist_tracks.playlist_id if not exists
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_playlist_tracks_playlist_id ON playlist_tracks(playlist_id)")
        print("  Created index: ix_playlist_tracks_playlist_id")
    except sqlite3.OperationalError as e:
        print(f"  Index ix_playlist_tracks_playlist_id: {e}")
    
    # Add index on playlist_tracks.track_id if not exists
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_playlist_tracks_track_id ON playlist_tracks(track_id)")
        print("  Created index: ix_playlist_tracks_track_id")
    except sqlite3.OperationalError as e:
        print(f"  Index ix_playlist_tracks_track_id: {e}")
    
    # Add index on favorites.user_id if not exists
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_favorites_user_id ON favorites(user_id)")
        print("  Created index: ix_favorites_user_id")
    except sqlite3.OperationalError as e:
        print(f"  Index ix_favorites_user_id: {e}")
    
    # Add index on favorites.track_id if not exists
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_favorites_track_id ON favorites(track_id)")
        print("  Created index: ix_favorites_track_id")
    except sqlite3.OperationalError as e:
        print(f"  Index ix_favorites_track_id: {e}")
    
    # Add user_id column to playlists if not exists
    cursor.execute("PRAGMA table_info(playlists)")
    columns = [row[1] for row in cursor.fetchall()]
    if "user_id" not in columns:
        cursor.execute("ALTER TABLE playlists ADD COLUMN user_id INTEGER REFERENCES users(id)")
        print("  Added column: playlists.user_id")
    
    # Add index on playlists.user_id if we just added it
    if "user_id" in columns:
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_playlists_user_id ON playlists(user_id)")
            print("  Created index: ix_playlists_user_id")
        except sqlite3.OperationalError as e:
            print(f"  Index ix_playlists_user_id: {e}")
    
    conn.commit()
    conn.close()
    
    print("Migration complete!")


if __name__ == "__main__":
    migrate()
