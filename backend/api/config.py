import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import yaml
from pathlib import Path

router = APIRouter(prefix="/api/config", tags=["config"])

class ConfigUpdate(BaseModel):
    music_path: str

@router.get("")
def get_config():
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    return {"library": {"music_path": ""}}

@router.post("")
def update_config(data: ConfigUpdate):
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    config["library"]["music_path"] = data.music_path
    
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    
    return {"saved": True}

@router.post("/migrate")
def run_migration():
    """Add missing columns to playback_state table"""
    from backend.models import engine
    import sqlite3
    
    conn = sqlite3.connect(engine.url.database)
    cursor = conn.cursor()
    
    # Check current columns
    cursor.execute("PRAGMA table_info(playback_state)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "queue" not in columns:
        cursor.execute("ALTER TABLE playback_state ADD COLUMN queue TEXT")
    
    if "shuffle_mode" not in columns:
        cursor.execute("ALTER TABLE playback_state ADD COLUMN shuffle_mode INTEGER DEFAULT 0")
    
    conn.commit()
    conn.close()
    
    return {"success": True, "columns": columns}