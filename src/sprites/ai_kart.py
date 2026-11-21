import pygame as pg
from math import sin, cos, pi, atan2, exp
from random import uniform

from src.sprites.kart import Kart, MAX_STEER_FRAMES, STEER_FRAME_ANGLE

vec = pg.math.Vector2



class AI_Kart(Kart):
    # AI kart that steers along a closed polygon (see Nature of Code path following)
    def __init__(self, game, path_points, kart_name, start_pos, start_angle):
        pg.sprite.Sprite.__init__(self, game.billboards)
        self.game = game
        self.name = kart_name
        self.effect_timers = {}  # effect name: seconds left
        self.set_sheet(kart_name)
        self.image = self.base_image
        self.rect = self.image.get_rect()
        self.depth = 0
        self.visible = False

        self.path_points = [vec(point) for point in path_points]
        self.path_radius = game.config["Gameplay.ai_path_radius"]       # px, no steering while inside
        # player's terminal speed on road: v = friction * (v + speed / FPS)
        friction = game.config["Gameplay.friction"]
        player_top_speed = friction * game.player.speed / game.config["Video.fps"] / (1 - friction)
        # same throttle and friction as the player -> same acceleration curve and top speed
        self.ai_speed_factor = game.config["Gameplay.ai_speed_factor"]
        self.friction = game.player.friction
        self.base_throttle = game.player.speed * self.ai_speed_factor
        self.throttle = self.base_throttle
        self.base_max_speed = player_top_speed * self.ai_speed_factor
        # force stays tied to base speed so handling doesn't change with variance
        self.max_force = game.config["Gameplay.ai_max_force"] * self.base_max_speed

        # speed variance: ease toward a random target that changes every few seconds
        self.speed_variance = game.config["Gameplay.ai_speed_variance"]
        self.speed_interval_min = game.config["Gameplay.ai_speed_interval_min"]
        self.speed_interval_max = game.config["Gameplay.ai_speed_interval_max"]
        self.speed_smoothing = game.config["Gameplay.ai_speed_smoothing"]
        self.variance_factor = 1.0
        self.target_variance_factor = 1.0
        self.time_until_variance_change = 0.0
        self.look_ahead_time = game.config["Gameplay.ai_look_ahead_time"]  # seconds
        self.steer_response_time = game.config["Gameplay.ai_steer_response_time"]
        self.separation_distance = game.config["Gameplay.ai_separation_distance"]  # in kart widths
        self.separation_weight = game.config["Gameplay.ai_separation_weight"]   # relative to path following
        self.target_ahead = game.config["Gameplay.ai_target_ahead"]      # px along the path
        self.item_delay_min = game.config["Gameplay.ai_item_delay_min"]
        self.item_delay_max = game.config["Gameplay.ai_item_delay_max"]
        self.time_until_item_use = None  # None = no item held

        self.map_pos = vec(start_pos)
        self.vel = vec()  # standing on the grid until the race starts
        self.acc = vec()

        self.angle = start_angle
        self.steer_yaw = 0.0
        self.turn_rate = 0.0  # rad/s, smoothed
        # player's turn rate at top speed -> full steering frames
        self.max_turn_rate = game.config["Gameplay.turn_force_fast"] * player_top_speed


    @property
    def pos(self):
        return self.map_pos


    def update_item(self, dt):
        # use a held item after a random delay
        if self.item is None:
            self.time_until_item_use = None
            return
        if self.time_until_item_use is None:
            self.time_until_item_use = uniform(self.item_delay_min, self.item_delay_max)
        self.time_until_item_use -= dt
        if self.time_until_item_use <= 0:
            self.use_item()


    def get_normal_point(self, point, segment_start, segment_end):
        # closest point to 'point' on the segment
        segment = segment_end - segment_start
        projection = (point - segment_start).dot(segment) / segment.length_squared()
        projection = max(0.0, min(1.0, projection))
        return segment_start + segment * projection


    def follow_path(self):
        predicted_pos = self.map_pos + self.vel * self.look_ahead_time
        closest_distance = float("inf")
        target = None
        point_count = len(self.path_points)
        for i in range(point_count):
            segment_start = self.path_points[i]
            segment_end = self.path_points[(i + 1) % point_count]
            normal_point = self.get_normal_point(predicted_pos, segment_start, segment_end)
            distance = predicted_pos.distance_to(normal_point)
            if distance < closest_distance:
                closest_distance = distance
                segment_direction = (segment_end - segment_start).normalize()
                target = normal_point + segment_direction * self.target_ahead

        if closest_distance > self.path_radius:
            self.seek(target)


    def seek(self, target):
        desired = target - self.map_pos
        if desired.length_squared() == 0:
            return
        if self.vel.length_squared() == 0:
            return
        desired.scale_to_length(self.vel.length())
        steer = (desired - self.vel) / self.steer_response_time
        # sideways steering only, throttle and friction handle speed like for the player
        heading = vec(cos(self.angle), sin(self.angle))
        side = vec(-heading.y, heading.x)
        steer = side * steer.dot(side)
        if steer.length() > self.max_force:
            steer.scale_to_length(self.max_force)
        self.acc += steer


    def separate(self):
        # steer away from karts that are too close (Nature of Code separation)
        min_distance = self.separation_distance * self.world_width
        push_sum = vec()
        count = 0
        for other in self.game.billboards:
            if other is self or not isinstance(other, Kart):
                continue
            offset = self.map_pos - other.map_pos
            distance = offset.length()
            if 0 < distance < min_distance:
                # 0 at edge of range, 1 when touching -> no on/off jump
                closeness = 1 - distance / min_distance
                push_sum += offset.normalize() * closeness
                count += 1
        if count == 0:
            return
        # sideways only, so separation doesn't brake or accelerate
        heading = vec(cos(self.angle), sin(self.angle))
        side = vec(-heading.y, heading.x)
        lateral_push = side * push_sum.dot(side)
        steer = lateral_push * self.max_force
        if steer.length() > self.max_force:
            steer.scale_to_length(self.max_force)
        self.acc += steer * self.separation_weight


    def accelerate(self):
        heading = vec(cos(self.angle), sin(self.angle))
        ground_speed = self.game.ground_speed_at(self.map_pos)
        self.acc += heading * self.throttle * ground_speed


    def update_speed_variance(self, dt):
        self.time_until_variance_change -= dt
        if self.time_until_variance_change <= 0:
            self.target_variance_factor = 1.0 + uniform(-self.speed_variance,
                                                        self.speed_variance)
            self.time_until_variance_change = uniform(self.speed_interval_min,
                                                      self.speed_interval_max)
        # framerate independent exponential smoothing
        blend = 1 - exp(-self.speed_smoothing * dt)
        self.variance_factor += (self.target_variance_factor - self.variance_factor) * blend
        # top speed scales linearly with throttle
        self.throttle = self.base_throttle * self.variance_factor * self.speed_factor


    def update(self, dt):
        if self.game.started:
            self.update_sheet_animation(dt)
            self.update_effects(dt)
            self.update_speed_variance(dt)
            self.update_item(dt)
            self.follow_path()
            self.separate()
            self.accelerate()

            self.vel += self.acc * dt
            self.map_pos += self.vel * dt
            self.acc *= 0
            self.vel *= self.friction
            self.update_steering(dt)


    def update_steering(self, dt):
        if dt <= 0 or self.vel.length_squared() == 0:
            return
        new_angle = atan2(self.vel.y, self.vel.x)
        angle_change = (new_angle - self.angle + pi) % (2 * pi) - pi
        self.angle = new_angle
        # low-pass filter so small corrections don't flicker
        smoothing = min(1.0, dt * 10)
        self.turn_rate += (angle_change / dt - self.turn_rate) * smoothing
        steer_frames = min(MAX_STEER_FRAMES,
                           round(abs(self.turn_rate) / self.max_turn_rate * MAX_STEER_FRAMES))
        steer_sign = 1 if self.turn_rate > 0 else -1
        self.steer_yaw = steer_sign * steer_frames * STEER_FRAME_ANGLE