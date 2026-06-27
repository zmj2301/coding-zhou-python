import sys
from pathlib import Path

from core import ConfigManager, TTSEngine, AudioHandler, AIEnhancer
from utils import HistoryManager
from ui import MainWindow


def main():
    base_dir = Path(__file__).parent
    
    config_manager = ConfigManager()
    tts_engine = TTSEngine(config_manager)
    audio_handler = AudioHandler(config_manager)
    ai_enhancer = AIEnhancer(config_manager)
    history_manager = HistoryManager(base_dir)
    
    app = MainWindow(config_manager, tts_engine, audio_handler, ai_enhancer, history_manager)
    app.mainloop()


if __name__ == "__main__":
    main()
