import pygame as pg
from random import choice, randint

vec = pg.math.Vector2



def lerp_colors(color, start, end, dist):
    # linear interpolation between two colors
    color.r, color.g, color.b = list(map(lambda x: int((x[0] * (1 - dist)) +
                                    (x[1] * dist)), zip(start[:3], end[:3])))



class Particle(pg.sprite.Sprite):
    def __init__(self, game, pos, images=None, colors=[], vel=vec(),
                 random_angle=0, vanish_speed=4, begin_size=1, end_size=1,
                 animation_frames=None, frame_duration=0.1):
        super().__init__(game.all_sprites)
        self.game = game

        # optional animation, plays once, then the particle dies
        self.animation_frames = animation_frames
        self.frame_duration = frame_duration  # seconds per frame
        self.time_passed = 0.0
        if animation_frames:
            images = [animation_frames[0]]

        if images:
            # if initialized with a list of images, choose one at random
            self.original_image = choice(images).copy()
            self.base_size = self.original_image.get_size()
            self.begin_size = begin_size  # scale factors, lerped over lifetime
            self.end_size = end_size
            self.size = self.scaled_size(begin_size)
            self.image = pg.transform.scale(self.original_image, self.size)
            self.rect = self.image.get_rect()
        else:
            # if not initialized with images, draw a circle
            self.image = pg.Surface((20, 20))
            self.image.set_colorkey((0, 0, 0))
            self.rect = self.image.get_rect()
            pg.draw.ellipse(self.image, (255, 255, 255), self.rect)

        self.colors = colors
        self.color = self.colors[0]
        self.alpha = 255

        if len(self.colors) > 1:
            self.prev_color = self.colors[0]
            self.target_color = self.colors[1]
            self.target_index = 1

        self.lerp_dist = 0
        self.lerp_speed = 0.07
        self.vanish_speed = vanish_speed
            
        self.pos = vec(pos)
        self.rect.center = self.pos
        # set random velocity vector
        self.vel = vel.rotate(randint(-random_angle, random_angle))
        
        self.forces = [self.vel] # additional forces to impact the vel
        
    
    def add_force(self, force, random_angle=0):
        self.forces.append(force.rotate(randint(-random_angle, random_angle)))
    
    
    def update(self, dt):
        if self.animation_frames:
            self.time_passed += dt
            frame_index = int(self.time_passed / self.frame_duration)
            if frame_index >= len(self.animation_frames):
                self.kill()
                return
            self.original_image = self.animation_frames[frame_index]

        # add velocity to position
        for f in self.forces:
            self.pos += f

        # update rect
        self.rect = self.image.get_rect()
        self.rect.center = self.pos
        
        # reduce alpha gradually
        self.alpha -= self.vanish_speed
        if self.alpha < 0:
            self.kill()
        else:
            self.color.a = int(self.alpha)
            
        size_scale = self.begin_size + (self.end_size - self.begin_size) * self.progress
        self.size = self.scaled_size(size_scale)
        
    
    @property
    def progress(self):
        # 0 at spawn, 1 at end of life
        if self.animation_frames:
            lifetime = len(self.animation_frames) * self.frame_duration
            return min(1.0, self.time_passed / lifetime)
        if self.vanish_speed > 0:
            return min(1.0, 1 - self.alpha / 255)
        return 0.0


    def scaled_size(self, scale):
        return [max(1, round(self.base_size[0] * scale)),
                max(1, round(self.base_size[1] * scale))]


    def draw(self, screen):
        self.blend_colors()
        self.image = self.original_image.copy()
        self.image = pg.transform.scale(self.image, self.size)
        self.image.fill(self.color, None, pg.BLEND_RGBA_MULT)
        
        screen.blit(self.image, self.rect)
        
    
    def blend_colors(self):
        if len(self.colors) > 1:
            if self.lerp_dist < 1:   
                # linear interpolation between previous and target color
                lerp_colors(self.color, self.prev_color, 
                            self.target_color, self.lerp_dist)
                self.lerp_dist += self.lerp_speed
            else:
                # if lerp distance reached 1, set the next target color
                self.target_index += 1
                if self.target_index < len(self.colors):
                    self.prev_color = self.target_color
                    self.target_color = self.colors[self.target_index]
                    self.lerp_dist = 0
                    
