from math import sin, cos, atan2, radians, degrees
from enum import Enum

from src.animation import Animation
from src.sprites.billboard import Billboard



# viewing angle of each kart frame in deg: 0 = behind, 90 = side (index 7), 180 = front
KART_FRAME_ANGLES = [i * 90 / 7 for i in range(8)] + [90 + i * 22.5 for i in range(1, 5)]
MAX_STEER_FRAMES = 5  # frames the kart turns visually at full steering
STEER_FRAME_ANGLE = radians(KART_FRAME_ANGLES[1])  # yaw per steering frame


class Direction(Enum):
    LEFT = 0
    RIGHT = 1


def get_kart_frame(images, flipped_images, yaw):
    # yaw in rad, positive = kart turned right relative to the view direction
    yaw_degrees = (degrees(yaw) + 180) % 360 - 180  # -180..180
    view_angle = abs(yaw_degrees)
    index = min(range(len(KART_FRAME_ANGLES)),
                key=lambda i: abs(KART_FRAME_ANGLES[i] - view_angle))
    return images[index] if yaw_degrees >= 0 else flipped_images[index]



class Kart(Billboard):
    # billboard using a kart spritesheet, needs angle, steer_yaw and map_pos
    item = None  # held item, set per instance on pickup

    def use_item(self):
        if self.item is None:
            return
        self.item.use(self.game, self)
        self.item = None


    def apply_effect(self, effect_name):
        duration = self.game.config[f"Gameplay.{effect_name}_duration"]
        self.effect_timers[effect_name] = duration


    def update_effects(self, dt):
        for effect_name in list(self.effect_timers):
            self.effect_timers[effect_name] -= dt
            if self.effect_timers[effect_name] <= 0:
                del self.effect_timers[effect_name]


    @property
    def speed_factor(self):
        factor = 1.0
        for effect_name in self.effect_timers:
            factor *= self.game.config[f"Gameplay.{effect_name}_speed_factor"]
        return factor


    def set_sheet(self, kart_name):
        # kart1, kart1_frame1, kart1_frame2, ... (extra sheets are optional)
        spritesheets = self.game.assets["spritesheets"]
        sheet_names = [kart_name]
        while f"{kart_name}_frame{len(sheet_names)}" in spritesheets:
            sheet_names.append(f"{kart_name}_frame{len(sheet_names)}")
        sheets = [(spritesheets[name], spritesheets[f"{name}_flipped"])
                  for name in sheet_names]
        frames_per_unit = self.game.config["Visuals.kart_frames_per_world_unit"]
        self.sheet_animation = Animation(sheets, frames_per_unit)
        self.base_image = sheets[0][0][0]


    def update_sheet_animation(self, dt):
        # animation speed follows driving speed
        self.sheet_animation.update(dt, self.vel.length())


    @property
    def world_width(self):
        # world size that projects to the native sprite width at kart distance
        mode7 = self.game.map
        screen_w = self.game.game_screen_rect.w
        frustum_dist = mode7.kart_ground_distance() / cos(mode7.fov_half)
        row_width = 2 * frustum_dist * sin(mode7.fov_half)
        width = self.base_image.get_width() * row_width / screen_w
        if "shrink" in self.effect_timers:
            width *= self.game.config["Gameplay.shrink_size_factor"]
        return width


    def project(self):
        # pick the frame from viewing angle + steering, then project as usual
        camera = self.game.camera
        to_kart = self.map_pos - camera.pos
        if to_kart.length_squared() > 0:
            view_angle = atan2(to_kart.y, to_kart.x)
        else:
            view_angle = camera.angle
        yaw = self.angle - view_angle + self.steer_yaw
        images, images_flipped = self.sheet_animation.current
        self.base_image = get_kart_frame(images, images_flipped, yaw)
        super().project()
        # locked kart skips world_width scaling, so apply shrink here
        if camera.is_locked_on(self) and "shrink" in self.effect_timers:
            shrink_factor = self.game.config["Gameplay.shrink_size_factor"]
            width = max(1, round(self.base_image.get_width() * shrink_factor))
            self.image = self.get_scaled_image(width)


    def draw(self, screen):
        # image can be smaller than rect (shrink), keep it on the ground
        if self.visible:
            bottom = self.rect.bottom - self.height_offset
            screen.blit(self.image, self.image.get_rect(midbottom=(self.rect.centerx, bottom)))
