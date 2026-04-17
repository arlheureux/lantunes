#!/usr/bin/env python3
"""Migration script to add indices and fix cascade deletes.

Run this script once to update the existing database schema.
"""
import sqlite3
import os

# Try multiple possible database locations
script_dir = os.path.dirname(os.path.abspath(__file__))
possible_db_paths = [
    "/root/lantunes/lantunes.db",
    os.path.join(script_dir, "..", "..", "lantunes.db"),
    os.path.join(os.getcwd(), "lantunes.db"),
    "/home/arnaud/dev/lantunes/lantunes.db",
]

db_path = None
for p in possible_db_paths:
    if os.path.exists(p):
        db_path = os.path.abspath(p)
        break

def migrate():
    if db_path is None:
        print("Database not found! Searched in:")
        for p in possible_db_paths:
            print(f"  {p}")
        print("\nFind the database with: python backend/scripts/find_database.py")
        return
    
    print(f"Using database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Starting migration...")
    
    # Check if database has any tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"Tables found: {tables}")
    
    if not tables:
        print("No tables found. Database may need to be initialized first by starting the server.")
        print("Run: python run.py (then Ctrl+C to stop)")
        conn.close()
        return
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Add index on albums.artist_id if table exists
    if 'albums' in tables:
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_albums_artist_id ON albums(artist_id)")
            print("  Created index: ix_albums_artist_id")
        except sqlite3.OperationalError as e:
            print(f"  Index ix_albums_artist_id: {e}")
    
    # Add index on tracks.album_id if table exists
    if 'tracks' in tables:
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_tracks_album_id ON tracks(album_id)")
            print("  Created index: ix_tracks_album_id")
        except sqlite3.OperationalError as e:
            print(f"  Index ix_tracks_album_id: {e}")
        
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_tracks_artist_id ON tracks(artist_id)")
            print("  Created index: ix_tracks_artist_id")
        except sqlite3.OperationalError as e:
            print(f"  Index ix_tracks_artist_id: {e}")
    
    # Add index on playlists.user_id if table exists
    if 'playlists' in tables:
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_playlists_user_id ON playlists(user_id)")
            print("  Created index: ix_playlists_user_id")
        except sqlite3.OperationalError as e:
            print(f"  Index ix_playlists_user_id: {e}")
    
    # Add index on playlist_tracks columns if table exists
    if 'playlist_tracks' in tables:
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_playlist_tracks_playlist_id ON playlist_tracks(playlist_id)")
            print("  Created index: ix_playlist_tracks_playlist_id")
        except sqlite3.OperationalError as e:
            print(f"  Index ix_playlist_tracks_playlist_id: {e}")
        
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_playlist_tracks_track_id ON playlist_tracks(track_id)")
            print("  Created index: ix_playlist_tracks_track_id")
        except sqlite3.OperationalError as e:
            print(f"  Index ix_playlist_tracks_track_id: {e}")
    
    # Add index on favorites columns if table exists
    if 'favorites' in tables:
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_favorites_user_id ON favorites(user_id)")
            print("  Created index: ix_favorites_user_id")
        except sqlite3.OperationalError as e:
            print(f"  Index ix_favorites_user_id: {e}")
        
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_favorites_track_id ON favorites(track_id)")
            print("  Created index: ix_favorites_track_id")
        except sqlite3.OperationalError as e:
            print(f"  Index ix_favorites_track_id: {e}")
    
    # Add user_id column to playlists if table exists and column doesn't
    if 'playlists' in tables:
        cursor.execute("PRAGMA table_info(playlists)")
        columns = [row[1] for row in cursor.fetchall()]
        if "user_id" not in columns:
            cursor.execute("ALTER TABLE playlists ADD COLUMN user_id INTEGER REFERENCES users(id)")
            print("  Added column: playlists.user_id")
    
    conn.commit()
    conn.close()
    
    print("Migration complete!")


if __name__ == "__main__":
    migrate()
