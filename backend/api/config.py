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