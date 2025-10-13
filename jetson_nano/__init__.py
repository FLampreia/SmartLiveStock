import yaml
from pathlib import Path
from threading import RLock

_config_static = {}
_lock = RLock()
_config_path = Path(__file__).parent / "config.yaml"

def load_static_config(path=None):
    global _config_static, _config_path
    if path:
        _config_path = Path(path)
    with _lock:
        with _config_path.open("r", encoding="utf-8") as f:
            _config_static = yaml.safe_load(f) or {}
    return _config_static

def get_static(*keys, default=None):
    """Access to static variables."""
    with _lock:
        node = _config_static
        for k in keys:
            if not isinstance(node, dict):
                return default
            node = node.get(k)
            if node is None:
                return default
        return node

# Load static config on import
load_static_config()
