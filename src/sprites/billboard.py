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
    shadow_images = {}  # (width, height) -> surface
    height = 0.0  # world units above the ground
    screen_scale = 1.0  # screen px per world unit, set in project()

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
            frustum_dist = self.depth / cos(mode7.fov_half)
            row_width = 2 * frustum_dist * sin(mode7.fov_half)
            self.screen_scale = self.game.game_screen_rect.w / row_width
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
        ground_y = round(depth * screen_rect.h + horizon_offset)
        row_width = 2 * frustum_dist * sin(mode7.fov_half)  # world units across screen
        screen_x = round((lateral / row_width + 0.5) * screen_rect.w)
        scale = screen_rect.w / row_width
        self.screen_scale = scale

        width = max(1, round(self.world_width * scale))
        if width > screen_rect.w * 2:  # too close, also keeps the cache small
            self.visible = False
            return
        self.image = self.get_scaled_image(width)
        # rect stays on the ground, height is applied when drawing
        self.rect = self.image.get_rect(midbottom=(screen_x, ground_y))
        elevated_rect = self.rect.move(0, -self.height_offset)
        self.visible = (self.rect.colliderect(screen_rect)
                        or elevated_rect.colliderect(screen_rect))


    @property
    def height_offset(self):
        # screen px between the ground point and the sprite bottom
        return round(self.height * self.screen_scale)


    def draw_shadow(self, screen):
        # dark ellipse on the floor below an elevated billboard
        if not self.visible or self.height <= 0:
            return
        config = self.game.config
        # shadow gets smaller the higher the sprite is
        size_factor = max(config["Visuals.shadow_min_size"],
                          1 - self.height / config["Visuals.shadow_fade_height"])
        shadow_width = max(2, round(self.image.get_width() * config["Visuals.shadow_width"] * size_factor))
        shadow_height = max(1, round(shadow_width * config["Visuals.shadow_squash"]))
        key = (shadow_width, shadow_height)
        if key not in Billboard.shadow_images:
            shadow = pg.Surface(key, pg.SRCALPHA)
            pg.draw.ellipse(shadow, (0, 0, 0, config["Visuals.shadow_alpha"]), shadow.get_rect())
            Billboard.shadow_images[key] = shadow
        shadow = Billboard.shadow_images[key]
        screen.blit(shadow, shadow.get_rect(center=self.rect.midbottom))


    def draw(self, screen):
        if self.visible:
            screen.blit(self.image, self.rect.move(0, -self.height_offset))