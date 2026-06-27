import pygame

class img_loading:
    def __init__(self,img_path):
        self.img = pygame.image.load(img_path)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("PVZ_pro")
        self.clock = pygame.time.Clock()
        self.running = True