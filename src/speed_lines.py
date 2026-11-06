import pygame as pg
from math import sin, cos, pi
from random import uniform

vec = pg.math.Vector2


class SpeedLines:
    # radial lines from the vanishing point, driven by the kart's speed factor

    def __init__(self, game):
        self.game = game
        self.config = game.config
        self.lines = []  # [angle, distance, length, time_left]
        self.spawn_timer = 0.0
        screen_rect = game.game_screen_rect
        self.surface = pg.Surface(screen_rect.size, pg.SRCALPHA)
        horizon_y = int(screen_rect.h * self.config["Visuals.horizon"])
        self.center = vec(screen_rect.centerx, horizon_y)


    def update(self, dt, speed_factor):
        config = self.config
        threshold = config["Visuals.speed_lines_threshold"]
        full = config["Visuals.speed_lines_full"]
        intensity = max(0.0, min(1.0, (speed_factor - threshold) / (full - threshold)))

        speed = config["Visuals.speed_lines_speed"]
        for line in self.lines:
            line[1] += speed * dt
            line[3] -= dt
        self.lines = [line for line in self.lines if line[3] > 0]

        if intensity == 0:
            self.spawn_timer = 0.0
            return
        interval = config["Visuals.speed_lines_interval"]
        self.spawn_timer += dt * intensity
        while self.spawn_timer >= interval:
            self.spawn_timer -= interval
            self.lines.append([
                uniform(0, 2 * pi),
                uniform(config["Visuals.speed_lines_min_distance"],
                        config["Visuals.speed_lines_max_distance"]),
                uniform(config["Visuals.speed_lines_min_length"],
                        config["Visuals.speed_lines_max_length"]),
                config["Visuals.speed_lines_lifetime"],
            ])


    def draw(self, screen):
        if not self.lines:
            return
        lifetime = self.config["Visuals.speed_lines_lifetime"]
        max_alpha = self.config["Visuals.speed_lines_alpha"]
        width = self.config["Visuals.speed_lines_width"]
        self.surface.fill((0, 0, 0, 0))
        for angle, distance, length, time_left in self.lines:
            direction = vec(cos(angle), sin(angle))
            start = self.center + direction * distance
            end = self.center + direction * (distance + length)
            alpha = int(max_alpha * time_left / lifetime)  # fade out
            pg.draw.line(self.surface, (255, 255, 255, alpha), start, end, width=width)
        screen.blit(self.surface, (0, 0))