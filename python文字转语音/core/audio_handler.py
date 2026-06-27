import os
from pathlib import Path
from pydub import AudioSegment


class AudioHandler:
    def __init__(self, config_manager):
        self.config_manager = config_manager
    
    def convert_audio_format(self, input_path, output_path, target_format):
        try:
            audio = AudioSegment.from_file(input_path)
            audio.export(output_path, format=target_format)
            return True
        except Exception as e:
            print(f"音频格式转换失败: {e}")
            return False
    
    def save_audio(self, source_path, target_path, target_format=None):
        try:
            if target_format is None:
                target_format = self.config_manager.get("output_format", "mp3")
            
            source_ext = Path(source_path).suffix[1:].lower()
            target_ext = Path(target_path).suffix[1:].lower()
            
            if not target_ext:
                target_path = f"{target_path}.{target_format}"
                target_ext = target_format
            
            if source_ext == target_ext:
                import shutil
                shutil.copy2(source_path, target_path)
                return True, target_path
            else:
                success = self.convert_audio_format(source_path, target_path, target_ext)
                return success, target_path
        except Exception as e:
            print(f"保存音频文件失败: {e}")
            return False, None
    
    def get_audio_duration(self, audio_path):
        try:
            audio = AudioSegment.from_file(audio_path)
            return len(audio) / 1000.0
        except Exception as e:
            print(f"获取音频时长失败: {e}")
            return 0
