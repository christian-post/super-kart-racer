import pygame as pg
from math import sin
from random import uniform

vec = pg.math.Vector2


def lerp_color(start, end, amount):
    return tuple(round(a + (b - a) * amount) for a, b in zip(start, end))


class ShrinkEffects:
    # lightning when a shrink item is used, wobbly tint while the player is shrunk

    def __init__(self, game):
        self.game = game
        self.config = game.config
        screen_rect = game.game_screen_rect
        self.surface = pg.Surface(screen_rect.size, pg.SRCALPHA)
        self.lightning_time_left = 0.0
        self.lightning_targets = []  # karts hit by the current strike
        self.bolts = []  # list of point lists, regenerated to flicker
        self.flicker_timer = 0.0
        self.tint_time = 0.0  # drives the color wobble
        self.player = None  # set in update


    def trigger_lightning(self, karts):
        self.lightning_time_left = self.config["Visuals.lightning_duration"]
        self.lightning_targets = list(karts)
        self.flicker_timer = 0.0


    def bolt_target(self, kart):
        # middle of the visible kart image (image can be smaller than rect)
        image_height = kart.image.get_height()
        return vec(kart.rect.centerx, kart.rect.bottom - kart.height_offset - image_height // 2)


    def build_bolt(self, target):
        segment_count = self.config["Visuals.lightning_segments"]
        jitter = self.config["Visuals.lightning_jitter"]
        start = vec(target.x + uniform(-jitter * 2, jitter * 2), 0)
        points = [start]
        for index in range(1, segment_count):
            amount = index / segment_count
            point = start.lerp(target, amount)
            point.x += uniform(-jitter, jitter)
            points.append(point)
        points.append(vec(target))
        return points


    def build_bolts(self):
        self.bolts = [self.build_bolt(self.bolt_target(kart))
                      for kart in self.lightning_targets
                      if kart.alive() and kart.visible]


    def update(self, dt, player):
        if self.lightning_time_left > 0:
            self.lightning_time_left -= dt
            self.flicker_timer -= dt
            if self.flicker_timer <= 0:
                self.flicker_timer = self.config["Visuals.lightning_flicker_interval"]
                self.build_bolts()
            if self.lightning_time_left <= 0:
                self.lightning_targets = []
                self.bolts = []

        if "shrink" in player.effect_timers:
            self.tint_time += dt
        else:
            self.tint_time = 0.0
        self.player = player


    def draw_lightning(self, screen):
        duration = self.config["Visuals.lightning_duration"]
        progress = 1 - self.lightning_time_left / duration  # 0 -> 1
        flash_alpha = round(self.config["Visuals.lightning_flash_alpha"] * (1 - progress) ** 2)
        self.surface.fill((255, 255, 255, flash_alpha))

        glow_color = self.config["Visuals.lightning_glow_color"]
        for points in self.bolts:
            pg.draw.lines(self.surface, (*glow_color, 200), False, points, width=3)
            pg.draw.lines(self.surface, (255, 255, 255, 255), False, points, width=1)
        screen.blit(self.surface, (0, 0))


    def draw_tint(self, screen):
        time_left = self.player.effect_timers["shrink"]
        fade_time = self.config["Visuals.shrink_tint_fade"]
        # fade in at the start, fade out at the end
        fade = min(1.0, self.tint_time / fade_time, time_left / fade_time)
        wobble = (sin(self.tint_time * self.config["Visuals.shrink_tint_speed"]) + 1) / 2
        color = lerp_color(self.config["Visuals.shrink_tint_color_a"],
                           self.config["Visuals.shrink_tint_color_b"], wobble)
        alpha = round(self.config["Visuals.shrink_tint_alpha"] * fade)
        self.surface.fill((*color, alpha))
        screen.blit(self.surface, (0, 0))


    def draw(self, screen):
        if self.player and "shrink" in self.player.effect_timers:
            self.draw_tint(screen)
        if self.lightning_time_left > 0:
            self.draw_lightning(screen)