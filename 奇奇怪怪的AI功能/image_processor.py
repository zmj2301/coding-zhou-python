import os
from pathlib import Path
from PIL import Image
import cv2
import numpy as np
from config import Config

class ImageProcessor:
    @staticmethod
    def is_supported_image(file_path):
        ext = Path(file_path).suffix.lower()
        return ext in Config.SUPPORTED_IMAGE_FORMATS
    
    @staticmethod
    def get_image_files(directory):
        image_files = []
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path) and ImageProcessor.is_supported_image(file_path):
                image_files.append(file_path)
        return sorted(image_files)
    
    @staticmethod
    def load_image(file_path):
        try:
            img = Image.open(file_path)
            img = img.convert('RGB')
            return img
        except Exception as e:
            raise Exception(f"无法加载图片 {file_path}: {str(e)}")
    
    @staticmethod
    def preprocess_image(image):
        img_array = np.array(image)
        
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        return Image.fromarray(enhanced)
