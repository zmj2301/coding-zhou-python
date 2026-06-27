import os
from paddleocr import PaddleOCR
from PIL import Image
import numpy as np
from config import Config

class OCRRecognizer:
    def __init__(self, lang='ch'):
        self.lang = lang
        self.ocr = None
    
    def _initialize(self):
        if self.ocr is None:
            self.ocr = PaddleOCR(lang=self.lang)
    
    def recognize(self, image):
        self._initialize()
        
        img_array = np.array(image)
        
        result = self.ocr.ocr(img_array)
        
        if not result or result[0] is None:
            return []
        
        recognized_text = []
        for line in result[0]:
            bbox = line[0]
            text_info = line[1]
            text = text_info[0]
            confidence = text_info[1]
            
            recognized_text.append({
                'text': text,
                'confidence': confidence,
                'bbox': bbox
            })
        
        return recognized_text
    
    def get_formatted_text(self, recognized_results):
        if not recognized_results:
            return ""
        
        sorted_results = sorted(recognized_results, key=lambda x: (x['bbox'][0][1], x['bbox'][0][0]))
        
        lines = []
        current_line = []
        current_y = None
        
        for item in sorted_results:
            bbox = item['bbox']
            y = (bbox[0][1] + bbox[2][1]) / 2
            
            if current_y is None or abs(y - current_y) < 30:
                current_line.append(item['text'])
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [item['text']]
            
            if current_y is None:
                current_y = y
            else:
                current_y = (current_y + y) / 2
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)
