import os

class Config:
    SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
    
    PDF_PAGE_SIZES = {
        'A4': (595.275590551, 841.88976378),
        'Letter': (612, 792),
        'Legal': (612, 1008)
    }
    
    DEFAULT_PAGE_SIZE = 'A4'
    DEFAULT_FONT = 'Helvetica'
    DEFAULT_FONT_SIZE = 12
    DEFAULT_MARGIN = 72
    
    OCR_LANGUAGE = 'ch'
    
    @staticmethod
    def ensure_dir(directory):
        if not os.path.exists(directory):
            os.makedirs(directory)
