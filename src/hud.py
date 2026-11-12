import pygame as pg

from src.sprites import Kart

vec = pg.math.Vector2

# posted by Game with attributes: lap (int), lap_time (float, seconds)
LAP_COMPLETED = pg.event.custom_type()


def build_minimap(tiled_map, size, layer_name="road",
                  road_color=(230, 230, 230, 220), bg_color=(0, 0, 0, 110)):
    # road tiles as pixel mask (1 px per tile), scaled to minimap size
    surf = pg.Surface((tiled_map.width, tiled_map.height), pg.SRCALPHA)
    surf.fill(bg_color)
    layer = tiled_map.get_layer_by_name(layer_name)
    for x, y, gid in layer.iter_data():
        if gid:
            surf.set_at((x, y), road_color)
    return pg.transform.scale(surf, size)


class HUD:
    # FONT_PATH = path.join(path.dirname(__file__), "..", "assets", "fonts", "PressStart2P.ttf")
    MAX_SPEED = 240  # max speed approximation, TODO set elswhere

    def __init__(self, race, tiled_map=None):
        self.race = race
        self.game = game = race.game
        # self.font = pg.font.Font(self.FONT_PATH, game.config["Hud.font_size"])
        # self.position_font = pg.font.Font(self.FONT_PATH, game.config["Hud.position_font_size"])
        self.font = self.game.assets["fonts"]["PressStart2P"][game.config["Hud.font_size"]]
        self.position_font = self.game.assets["fonts"]["PressStart2P"][game.config["Hud.position_font_size"]]
        minimap_s = game.config["Hud.minimap_size"]
        self.minimap = build_minimap(tiled_map, (minimap_s, minimap_s)) if tiled_map else None
        self.MARGIN = game.config["Hud.margin"]
        self.last_lap_time = None
        self.lap_time_until = 0  # pg.time.get_ticks() timestamp
        item_frame_size = game.config["Hud.item_frame_size"]
        self.item_frame = pg.Surface((item_frame_size, item_frame_size), pg.SRCALPHA)
        self.item_frame.fill((0, 0, 0, 110))


    def handle_event(self, event):
        if event.type == LAP_COMPLETED:
            self.last_lap_time = event.lap_time
            self.lap_time_until = pg.time.get_ticks() + self.game.config["Hud.lap_time_showing_duration"] * 1000


    @staticmethod
    def format_time(t):
        m, s = divmod(t, 60)
        return f"{int(m):02d}:{s:05.2f}"


    def draw_text(self, screen, text, pos, anchor="topright", font=None):
        # no antialiasing to keep hard pixel edges
        font = font or self.font
        shadow = font.render(text, False, (0, 0, 0))
        surf = font.render(text, False, (255, 255, 255))
        rect = surf.get_rect(**{anchor: pos})
        screen.blit(shadow, rect.move(1, 1))
        screen.blit(surf, rect)
        return rect


    def draw_lap_and_time(self, screen):
        r = self.race
        lap = min(r.current_lap, r.course.max_laps)
        self.draw_text(screen, f"LAP {lap}/{r.course.max_laps}",
                       (self.MARGIN, self.MARGIN), anchor="topleft")
        right = screen.get_width() - self.MARGIN
        r = self.draw_text(screen, f"TIME {self.format_time(r.race_time)}",
                           (right, self.MARGIN))

        # last lap time, shown briefly after finishing a lap
        if self.last_lap_time is not None and pg.time.get_ticks() < self.lap_time_until:
            self.draw_text(screen, f"LAP {self.format_time(self.last_lap_time)}",
                           (right, r.bottom))


    def draw_speedometer(self, screen):
        num_speed_bars = self.game.config["Hud.speed_bars"]
        bar_w = self.game.config["Hud.speed_bar_w"]
        bar_gap = self.game.config["Hud.speed_bar_gap"]
        bar_min_h = self.game.config["Hud.speed_bar_min_h"]
        bar_step_h = self.game.config["Hud.speed_bar_step_h"]

        frac = min(self.game.player.vel.length() / self.MAX_SPEED, 1.0)
        lit = round(frac * num_speed_bars)
        x = self.MARGIN
        bottom = screen.get_height() - self.MARGIN

        for i in range(num_speed_bars):
            h = bar_min_h + i * bar_step_h
            rect = pg.Rect(x, bottom - h, bar_w, h)
            if i < lit:
                t = i / max(num_speed_bars - 1, 1)
                color = (int(80 + 175 * t), int(230 - 150 * t), 60)  # green -> red
            else:
                color = (60, 60, 60)
            pg.draw.rect(screen, (0, 0, 0), rect.inflate(2, 2))
            pg.draw.rect(screen, color, rect)
            x += bar_w + bar_gap


    def draw_minimap(self, screen):
        if self.minimap is None:
            return
        mw = mh = self.game.config["Hud.minimap_size"]
        rect = self.minimap.get_rect(bottomright=(screen.get_width() - self.MARGIN,
                                                  screen.get_height() - self.MARGIN))
        screen.blit(self.minimap, rect)
        pg.draw.rect(screen, (255, 255, 255), rect.inflate(2, 2), 1)

        map_w = self.race.course.pixel_width
        map_h = self.race.course.pixel_height

        def to_minimap(map_pos):
            return vec(rect.x + min(max(map_pos.x / map_w, 0), 1) * mw,
                       rect.y + min(max(map_pos.y / map_h, 0), 1) * mh)

        # AI karts first, so the player is drawn on top
        for kart in self.game.billboards:
            if not isinstance(kart, Kart) or kart is self.game.player:
                continue
            dot = to_minimap(kart.map_pos)
            pg.draw.rect(screen, (60, 140, 255), (int(dot.x) - 1, int(dot.y) - 1, 2, 2))

        # player as single pixel + heading pixel (dot)
        player = self.game.player
        dot = to_minimap(player.pos)
        tip = dot + vec(2, 0).rotate_rad(player.angle)
        screen.set_at((int(tip.x), int(tip.y)), (255, 200, 60))
        pg.draw.rect(screen, (255, 60, 60), (int(dot.x) - 1, int(dot.y) - 1, 2, 2))


    def draw_position(self, screen):
        standings = self.race.standings
        if standings is None:
            return
        config = self.game.config
        speedometer_h = (config["Hud.speed_bar_min_h"]
                         + (config["Hud.speed_bars"] - 1) * config["Hud.speed_bar_step_h"])
        bottom = screen.get_height() - self.MARGIN - speedometer_h - 3
        position = standings.position_of(self.game.player)
        # big position number, small "/N" on the same baseline
        baseline = bottom + self.position_font.get_descent()  # descent is negative
        position_rect = self.draw_text(
            screen, str(position),
            (self.MARGIN, baseline - self.position_font.get_ascent()),
            anchor="topleft", font=self.position_font)
        self.draw_text(screen, f"/{len(standings.karts)}",
                       (position_rect.right, baseline - self.font.get_ascent()),
                       anchor="topleft")


    def draw_item(self, screen):
        # empty slot is always shown, below the lap counter
        top = self.MARGIN + self.font.get_height() + 3
        rect = self.item_frame.get_rect(topleft=(self.MARGIN + 1, top))
        screen.blit(self.item_frame, rect)
        pg.draw.rect(screen, (255, 255, 255), rect.inflate(2, 2), 1)
        item = getattr(self.game.player, "item", None)  # AI karts have no slot
        if item is not None:
            portrait = self.game.assets["portraits"][f"item_{item.name}"]
            screen.blit(portrait, portrait.get_rect(center=rect.center))


    def find_rivals_behind(self):
        # all AI karts behind the player within warning range, farthest first
        # returns list of (kart, gap)
        standings = self.race.standings
        if standings is None:
            return []
        player = self.game.player
        max_distance = self.game.config["Hud.rival_warning_distance"]
        min_distance = self.game.config["Hud.rival_warning_min_distance"]
        rivals = []
        for kart in standings.karts:
            if kart is player or kart in standings.finish_order:
                continue
            gap = standings.progress[player] - standings.progress[kart]
            if min_distance < gap < max_distance:
                rivals.append((kart, gap))
        rivals.sort(key=lambda rival_and_gap: rival_and_gap[1], reverse=True)
        return rivals


    def draw_rival_warning(self, screen, rival, gap):
        config = self.game.config
        icon_index = int(rival.name.removeprefix("kart")) - 1
        icon = self.game.assets["spritesheets"]["kart_icons"][icon_index]

        # size: max scale at min distance, min scale at max distance
        min_distance = config["Hud.rival_warning_min_distance"]
        max_distance = config["Hud.rival_warning_distance"]
        distance_fraction = (gap - min_distance) / max(max_distance - min_distance, 1)
        min_scale = config["Hud.rival_icon_min_scale"]
        max_scale = config["Hud.rival_icon_max_scale"]
        scale = max_scale + (min_scale - max_scale) * distance_fraction
        icon_size = (max(1, round(icon.get_width() * scale)),
                     max(1, round(icon.get_height() * scale)))
        icon = pg.transform.scale(icon, icon_size)

        # x: sideways offset of the rival in camera space, -1 (left) .. 1 (right)
        camera = self.game.camera
        to_rival = rival.map_pos - self.game.player.map_pos
        rival_distance = to_rival.length()
        side_fraction = 0.0
        if rival_distance > 0:
            camera_right = vec(-camera.forward.y, camera.forward.x)
            side_fraction = to_rival.dot(camera_right) / rival_distance
        center_x = screen.get_width() // 2 + int(side_fraction * config["Hud.rival_max_x_offset"])

        padding = config["Hud.rival_frame_padding"]
        arrow_size = config["Hud.rival_arrow_size"]
        arrow_tip_y = screen.get_height() - self.MARGIN

        frame_rect = icon.get_rect().inflate(padding * 2, padding * 2)
        frame_rect.midbottom = (center_x, arrow_tip_y - arrow_size - 1)
        frame = pg.Surface(frame_rect.size, pg.SRCALPHA)
        frame.fill((0, 0, 0, 110))
        screen.blit(frame, frame_rect)
        pg.draw.rect(screen, (255, 255, 255), frame_rect.inflate(2, 2), 1)
        screen.blit(icon, icon.get_rect(center=frame_rect.center))

        # arrow below the frame, pointing down
        arrow_top_y = frame_rect.bottom + 1
        arrow_points = [(center_x - arrow_size, arrow_top_y),
                        (center_x + arrow_size, arrow_top_y),
                        (center_x, arrow_tip_y)]
        pg.draw.polygon(screen, (255, 255, 255), arrow_points)


    def draw(self, screen):
        self.draw_lap_and_time(screen)
        self.draw_item(screen)
        self.draw_speedometer(screen)
        self.draw_minimap(screen)
        self.draw_position(screen)
        for rival, gap in self.find_rivals_behind():
            self.draw_rival_warning(screen, rival, gap)