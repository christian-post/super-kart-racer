import pygame as pg
from math import sin, cos

from src.animation import Animation


vec = pg.math.Vector2


class Billboard(pg.sprite.Sprite):
    # static world sprite from a Tiled object, image = assets/<name>.png
    # scaled images get cached to avoid constant scaling operations
    base_images = {}  # name -> surface
    scaled_images = {}  # (name, width) -> surface
    subclasses_by_tiled_name = {}  # filled by __init_subclass__

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Billboard.subclasses_by_tiled_name[cls.__name__.lower()] = cls


    def __init__(self, game, tiled_object):
        super().__init__(game.billboards)
        self.game = game
        self.name = tiled_object.name
        # ground point = center of the object rect
        self.map_pos = vec(tiled_object.x + tiled_object.width / 2,
                           tiled_object.y + tiled_object.height / 2)
        self.world_width = tiled_object.width  # size on the map, set in Tiled

        if self.name not in Billboard.base_images:
            Billboard.base_images[self.name] = game.assets["sprites"].get(self.name)
        self.animation = None
        sheet = game.assets["spritesheets"].get(self.name)
        if sheet:
            fps = game.config["Assets.animation_fps"][self.name]
            self.animation = Animation(sheet, fps)
            self.base_image = sheet[0]
        else:
            self.base_image = Billboard.base_images[self.name]
        self.image = self.base_image
        self.rect = self.image.get_rect()
        self.depth = 0
        self.visible = False


    def get_scaled_image(self, width):
        key = (id(self.base_image), width)
        if key not in Billboard.scaled_images:
            aspect = self.base_image.get_height() / self.base_image.get_width()
            height = max(1, round(width * aspect))
            Billboard.scaled_images[key] = pg.transform.scale(self.base_image, (width, height))
        return Billboard.scaled_images[key]


    def update(self, dt):
        # moving subclasses override this
        if self.animation:
            self.animation.update(dt)
            self.base_image = self.animation.current


    def project(self):
        # world -> screen, call after the camera moved
        mode7 = self.game.map
        camera = self.game.camera
        if camera.is_locked_on(self):
            # fixed kart spot, no jitter
            self.image = self.base_image
            self.depth = mode7.kart_ground_distance()
            self.visible = True
            return
        screen_rect = self.game.game_screen_rect
        horizon_offset = int(screen_rect.h * self.game.config["Visuals.horizon"])

        relative = self.map_pos - camera.pos

        forward_dir = camera.forward
        right_dir = vec(-forward_dir.y, forward_dir.x)
        forward = relative.dot(forward_dir)
        lateral = relative.dot(right_dir)
        self.depth = forward

        # inverse of render_mode7: distance along frustum edge -> screen row
        frustum_dist = forward / cos(mode7.fov_half)
        if frustum_dist <= mode7.near:
            self.visible = False
            return
        depth = (mode7.far - mode7.near) / (frustum_dist - mode7.near)
        ground_y = depth * screen_rect.h + horizon_offset
        row_width = 2 * frustum_dist * sin(mode7.fov_half)  # world units across screen
        screen_x = (lateral / row_width + 0.5) * screen_rect.w
        scale = screen_rect.w / row_width

        width = max(1, int(self.world_width * scale))
        if width > screen_rect.w * 2:  # too close, also keeps the cache small
            self.visible = False
            return
        self.image = self.get_scaled_image(width)
        self.rect = self.image.get_rect(midbottom=(screen_x, ground_y))
        self.visible = self.rect.colliderect(screen_rect)


    def draw(self, screen):
        if self.visible:
            screen.blit(self.image, self.rect)