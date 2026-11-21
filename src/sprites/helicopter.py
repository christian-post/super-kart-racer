import pygame as pg
from enum import Enum, auto
from math import sin, cos, pi

from src.animation import Animation
from src.sprites.billboard import Billboard

vec = pg.math.Vector2


class RescuePhase(Enum):
    APPROACH = auto()  # fly to the kart
    LIFT = auto()      # pull the kart up
    CARRY = auto()     # fly to the drop position
    DROP = auto()      # lower the kart onto the road
    LEAVE = auto()     # fly away, kart is free again


CARRYING_PHASES = (RescuePhase.LIFT, RescuePhase.CARRY, RescuePhase.DROP)


def smoothstep(t):
    # 0..1 -> 0..1, eases in and out
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def lerp(start, end, t):
    return start + (end - start) * t


class Helicopter(Billboard):
    # picks up a kart from the killzone and drops it at drop_pos
    def __init__(self, game, kart, drop_pos, drop_angle):
        pg.sprite.Sprite.__init__(self, game.billboards)
        self.game = game
        self.name = "helicopter"
        self.kart = kart
        self.drop_pos = vec(drop_pos)
        self.drop_angle = drop_angle  # kart faces this way after the drop
        self.carry_start_angle = 0.0
        self.carry_angle_change = 0.0
        self.pickup_pos = vec(kart.map_pos)

        # sheet faces left, keep (left, right) pairs per frame
        frames = game.assets["spritesheets"]["helicopter"]
        frame_pairs = [(frame, pg.transform.flip(frame, True, False)) for frame in frames]
        self.animation = Animation(frame_pairs, game.config["Assets.animation_fps"]["helicopter"])
        self.facing_right = False
        self.base_image = frames[0]
        self.image = self.base_image
        self.rect = self.image.get_rect()
        self.depth = 0
        self.visible = False

        # same pixel density as the karts at their screen spot
        mode7 = game.map
        frustum_dist = mode7.kart_ground_distance() / cos(mode7.fov_half)
        row_width = 2 * frustum_dist * sin(mode7.fov_half)
        self.world_units_per_pixel = row_width / game.game_screen_rect.w
        self.world_width = self.base_image.get_width() * self.world_units_per_pixel

        # come in from far ahead, high up
        self.approach_start_pos = kart.map_pos + game.camera.forward * self.setting("spawn_distance")
        self.approach_start_height = self.setting("spawn_height")
        self.map_pos = vec(self.approach_start_pos)
        self.height = self.approach_start_height
        self.carry_height = 0.0  # kart height without bobbing
        self.carry_duration = 0.0
        self.leave_start_pos = vec()
        self.leave_end_pos = vec()
        self.leave_start_height = 0.0
        self.time_passed = 0.0

        # kart loses control right away
        kart.vel *= 0
        kart.steer_yaw = 0.0
        self.start_phase(RescuePhase.APPROACH)


    def setting(self, key):
        return self.game.config[f"Helicopter.{key}"]


    @property
    def hang_distance(self):
        # kart top hangs at the skids
        return self.kart.base_image.get_height() * self.world_units_per_pixel


    def start_phase(self, phase):
        self.phase = phase
        self.phase_time = 0.0
        if phase == RescuePhase.CARRY:
            distance = self.pickup_pos.distance_to(self.drop_pos)
            self.carry_duration = max(self.setting("min_carry_duration"),
                                      distance / self.setting("carry_speed"))
            # turn the shorter way, -pi..pi
            self.carry_start_angle = self.kart.angle
            self.carry_angle_change = (self.drop_angle - self.kart.angle + pi) % (2 * pi) - pi
        elif phase == RescuePhase.LEAVE:
            self.leave_start_pos = vec(self.map_pos)
            self.leave_end_pos = self.map_pos + self.game.camera.forward * self.setting("spawn_distance")
            self.leave_start_height = self.height


    def release_kart(self):
        self.kart.height = 0.0
        self.kart.vel *= 0
        self.kart.helicopter = None


    def update(self, dt):
        self.time_passed += dt
        self.phase_time += dt
        self.animation.update(dt)
        previous_pos = vec(self.map_pos)

        # kart got replaced (race finished) -> just fly away
        if not self.kart.alive() and self.phase != RescuePhase.LEAVE:
            self.start_phase(RescuePhase.LEAVE)

        if self.phase == RescuePhase.APPROACH:
            progress = smoothstep(self.phase_time / self.setting("approach_duration"))
            self.map_pos = self.approach_start_pos.lerp(self.pickup_pos, progress)
            self.height = lerp(self.approach_start_height, self.hang_distance, progress)
            if progress >= 1:
                self.start_phase(RescuePhase.LIFT)

        elif self.phase == RescuePhase.LIFT:
            progress = smoothstep(self.phase_time / self.setting("lift_duration"))
            self.map_pos = vec(self.pickup_pos)
            self.carry_height = self.setting("lift_height") * progress
            if progress >= 1:
                self.start_phase(RescuePhase.CARRY)

        elif self.phase == RescuePhase.CARRY:
            progress = smoothstep(self.phase_time / self.carry_duration)
            self.map_pos = self.pickup_pos.lerp(self.drop_pos, progress)
            self.carry_height = self.setting("lift_height")
            self.kart.angle = self.carry_start_angle + self.carry_angle_change * progress
            if progress >= 1:
                self.start_phase(RescuePhase.DROP)

        elif self.phase == RescuePhase.DROP:
            progress = smoothstep(self.phase_time / self.setting("drop_duration"))
            self.map_pos = vec(self.drop_pos)
            self.carry_height = self.setting("lift_height") * (1 - progress)
            if progress >= 1:
                self.release_kart()
                self.start_phase(RescuePhase.LEAVE)

        elif self.phase == RescuePhase.LEAVE:
            progress = self.phase_time / self.setting("leave_duration")
            accelerate = progress * progress  # slow start, then off it goes
            self.map_pos = self.leave_start_pos.lerp(self.leave_end_pos, min(accelerate, 1))
            self.height = lerp(self.leave_start_height, self.setting("leave_height"), min(accelerate, 1))
            if progress >= 1:
                self.kill()
                return

        if self.phase in CARRYING_PHASES:
            # no bobbing while the kart touches the ground
            bob_factor = self.carry_height / self.setting("lift_height")
            bob = sin(self.time_passed * self.setting("bob_speed")) * self.setting("bob_amplitude") * bob_factor
            self.kart.height = self.carry_height + bob
            self.kart.pos.update(self.map_pos)
            self.height = self.kart.height + self.hang_distance

        self.update_facing(self.map_pos - previous_pos)


    def update_facing(self, movement):
        # flip the side view depending on the screen direction of movement
        forward = self.game.camera.forward
        camera_right = vec(-forward.y, forward.x)
        lateral = movement.dot(camera_right)
        if abs(lateral) > 0.01:
            self.facing_right = lateral > 0
        facing_left_image, facing_right_image = self.animation.current
        self.base_image = facing_right_image if self.facing_right else facing_left_image


    def project(self):
        super().project()
        if self.phase in CARRYING_PHASES:
            # same ground point as the kart, draw on top so the hook covers it
            self.depth -= 0.1