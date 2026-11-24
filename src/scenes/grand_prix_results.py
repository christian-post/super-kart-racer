import pygame as pg

from src.scenes.scene import Scene


class GrandPrixResults(Scene):
    """Overall grand prix ranking, drawn over the finished race."""

    transparent = True

    def __init__(self, game, race=None, **kwargs):
        super().__init__(game)
        self.race = race  # keeps running in the background


    def get_event(self, event):
        if event.type != pg.KEYDOWN or event.key != pg.K_RETURN:
            return
        grand_prix = self.game.grand_prix
        if grand_prix.is_last_race:
            self.game.grand_prix = None
            self.game.switch_scene("ModeSelect")
        else:
            grand_prix.next_race()
            self.game.switch_scene("Race", course_name=grand_prix.current_course_name,
                                   kart_name=grand_prix.player_kart_name)


    def update(self, dt):
        self.race.update(dt)


    def draw(self, screen):
        shade = pg.Surface(screen.get_size(), pg.SRCALPHA)
        shade.fill((0, 0, 0, 140))
        screen.blit(shade, (0, 0))

        grand_prix = self.game.grand_prix
        center_x = screen.get_width() // 2
        if grand_prix.is_last_race:
            title = "FINAL RESULTS"
        else:
            title = f"RACE {grand_prix.race_index + 1}/{len(grand_prix.course_names)}"
        self.draw_text(screen, title, (center_x, 40), "yellow")

        # one row per kart: position, icon, total points, points of the last race
        row_height = 19
        column_gap = 6
        icons = self.game.assets["spritesheets"]["kart_icons"]
        icon_width = icons[0].get_width()
        position_width = self.game.font.size("0.")[0]
        points_width = self.game.font.size("000")[0]
        gained_width = self.game.font.size("+00")[0]
        row_width = position_width + icon_width + points_width + gained_width + 3 * column_gap

        position_x = (screen.get_width() - row_width) // 2
        icon_x = position_x + position_width + column_gap
        points_x = icon_x + icon_width + column_gap
        gained_x = points_x + points_width + column_gap

        y = 52
        for position, kart_name in enumerate(grand_prix.overall_ranking(), start=1):
            center_y = y + row_height // 2
            color = "yellow" if kart_name == grand_prix.player_kart_name else "white"
            self.draw_text(screen, f"{position}.", (position_x, center_y), color, anchor="midleft")
            icon = icons[int(kart_name.removeprefix("kart")) - 1]
            screen.blit(icon, icon.get_rect(midleft=(icon_x, center_y)))
            self.draw_text(screen, str(grand_prix.points[kart_name]), (points_x, center_y),
                           color, anchor="midleft")
            self.draw_text(screen, f"+{grand_prix.last_race_points[kart_name]}", (gained_x, center_y),
                           "gray60", anchor="midleft")
            y += row_height

        self.draw_text(screen, "Enter: continue", (center_x, y + 12))