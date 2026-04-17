import sys
import os
import fcntl
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import yaml
from pathlib import Path
import requests
from dependencies import get_current_user, require_admin

router = APIRouter(prefix="/api/config", tags=["config"])

class ConfigUpdate(BaseModel):
    music_path: str

class TestServerRequest(BaseModel):
    url: str


@router.get("")
def get_config(current_user = Depends(get_current_user)):
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    return {"library": {"music_path": ""}}


@router.post("")
def update_config(data: ConfigUpdate, current_user = Depends(require_admin)):
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    
    music_path = data.music_path.strip()
    
    if music_path:
        abs_music_path = os.path.abspath(music_path)
        forbidden_paths = ['/etc', '/root', '/home', '/var', '/usr', '/bin', '/sbin', '/sys', '/proc', '/dev', '/boot', '/srv', '/opt', '/mnt', '/media']
        if ".." in music_path or any(abs_music_path.startswith(fp) for fp in forbidden_paths):
            raise HTTPException(status_code=400, detail="Invalid path")
    
    lock_path = str(config_path) + ".lock"
    with open(lock_path, 'w') as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            
            config.setdefault("library", {})["music_path"] = music_path
            
            with open(config_path, 'w') as f:
                yaml.dump(config, f)
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
    
    os.remove(lock_path)
    return {"saved": True}


@router.post("/test")
async def test_server(data: TestServerRequest, current_user = Depends(get_current_user)):
    """Test server URL - runs server-side to avoid CORS and keep auth"""
    test_url = data.url.strip()
    
    if not test_url:
        raise HTTPException(status_code=400, detail="URL required")
    
    if not test_url.startswith("http://") and not test_url.startswith("https://"):
        test_url = "http://" + test_url
    
    try:
        response = requests.get(test_url + "/api/config", timeout=5)
        if response.ok:
            return {"success": True, "url": test_url}
        else:
            return {"success": False, "error": f"Server returned {response.status_code}"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Connection timed out"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Could not connect to server"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_migration():
    """Add missing columns to playback_state and download_jobs tables"""
    from backend.models import engine
    import sqlite3
    
    conn = sqlite3.connect(engine.url.database)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(playback_state)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "queue" not in columns:
        cursor.execute("ALTER TABLE playback_state ADD COLUMN queue TEXT")
    
    if "shuffle_mode" not in columns:
        cursor.execute("ALTER TABLE playback_state ADD COLUMN shuffle_mode INTEGER DEFAULT 0")
    
    if "repeat" not in columns:
        cursor.execute("ALTER TABLE playback_state ADD COLUMN repeat TEXT DEFAULT 'off'")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='download_jobs'")
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE download_jobs (
                id INTEGER PRIMARY KEY,
                playlist_id INTEGER,
                status TEXT DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                total INTEGER DEFAULT 0,
                error TEXT,
                zip_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
    
    conn.commit()
    conn.close()
