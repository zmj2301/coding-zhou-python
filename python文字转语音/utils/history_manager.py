import json
from pathlib import Path
from datetime import datetime


class HistoryManager:
    def __init__(self, base_dir):
        self.data_dir = Path(base_dir) / "data"
        self.history_path = self.data_dir / "history.json"
        self.history = self.load_history()
    
    def load_history(self):
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)
        
        if self.history_path.exists():
            try:
                with open(self.history_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载历史记录失败: {e}")
                return []
        else:
            return []
    
    def save_history(self):
        try:
            if not self.data_dir.exists():
                self.data_dir.mkdir(parents=True, exist_ok=True)
            with open(self.history_path, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存历史记录失败: {e}")
            return False
    
    def add_record(self, text, audio_path, settings):
        record = {
            "id": len(self.history) + 1,
            "text": text[:200] + "..." if len(text) > 200 else text,
            "full_text": text,
            "audio_path": audio_path,
            "settings": settings,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.history.insert(0, record)
        
        if len(self.history) > 100:
            self.history = self.history[:100]
        
        self.save_history()
        return record
    
    def get_history(self, limit=50):
        return self.history[:limit]
    
    def clear_history(self):
        self.history = []
        self.save_history()
    
    def delete_record(self, record_id):
        self.history = [r for r in self.history if r["id"] != record_id]
        self.save_history()
