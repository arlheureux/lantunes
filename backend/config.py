import yaml
from pathlib import Path

def get_config_path():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_in_project = project_root / "config.yaml"
    config_in_backend = script_dir / "config.yaml"
    
    if config_in_project.exists():
        return config_in_project
    elif config_in_backend.exists():
        return config_in_backend
    else:
        return config_in_project

CONFIG_PATH = get_config_path()

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f)
    return {
        "server": {"host": "0.0.0.0", "port": 8080},
        "library": {"music_path": "", "scan_on_startup": False},
        "dlna": {"enabled": False, "friendly_name": "LanTunes"}
    }

config = load_config()