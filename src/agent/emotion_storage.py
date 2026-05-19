import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional


class EmotionStateStorage:
    """基于 JSON 文件的情绪状态持久化存储。"""
    
    def __init__(self, storage_dir: str | None = None):
        if storage_dir is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            storage_dir = str(project_root / "storage")
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.storage_dir / "emotion_state.json"
    
    def save(self, state_data: Dict[str, Any]) -> bool:
        """保存情绪状态到 JSON 文件。"""
        try:
            state_data["saved_at"] = time.time()
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save emotion state: {e}")
            return False
    
    def load(self) -> Optional[Dict[str, Any]]:
        """从 JSON 文件加载情绪状态。"""
        if not self.state_file.exists():
            return None
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"Failed to load emotion state: {e}")
            return None
    
    def clear(self) -> bool:
        """清除保存的情绪状态。"""
        if self.state_file.exists():
            try:
                os.remove(self.state_file)
                return True
            except Exception:
                return False
        return True
