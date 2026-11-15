import pygame as pg


class TrafficLight(pg.sprite.Sprite):
    def __init__(self, game, pos):
        super().__init__(game.all_sprites)
        self.game = game
        self.images = game.assets["spritesheets"]["lights"]
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.done = False
        self.timer = 0
        self.img_index = 0
        
    
    def update(self, dt):
        self.timer += dt
        if self.timer >= 1:
            self.timer = 0
            self.img_index += 1
            if self.img_index == 4:
                self.done = True
            try:
                self.image = self.images[self.img_index]
            except:
                self.kill()
        

    def draw(self, screen):
        screen.blit(self.image, self.rect)