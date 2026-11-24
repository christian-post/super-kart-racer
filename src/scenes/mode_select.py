import pygame as pg

from src.scenes.scene import Scene
from src.game_mode import GameMode


class ModeSelect(Scene):
    def __init__(self, game, **kwargs):
        super().__init__(game)
        self.modes = list(GameMode)
        self.selected_index = self.modes.index(GameMode.SINGLE_RACE)


    def get_event(self, event):
        if event.type != pg.KEYDOWN:
            return
        if event.key == pg.K_ESCAPE:
            self.game.switch_scene("TitleScreen")
        elif event.key in (pg.K_w, pg.K_UP):
            self.selected_index = (self.selected_index - 1) % len(self.modes)
        elif event.key in (pg.K_s, pg.K_DOWN):
            self.selected_index = (self.selected_index + 1) % len(self.modes)
        elif event.key in (pg.K_RETURN, pg.K_SPACE):
            mode = self.modes[self.selected_index]
            if mode.is_available:
                self.game.mode = mode
                self.game.switch_scene("CourseSelect")


    def draw(self, screen):
        screen.fill(pg.Color("black"))
        center_x = screen.get_width() // 2
        self.draw_text(screen, "SELECT MODE", (center_x, 20))

        for index, mode in enumerate(self.modes):
            is_selected = index == self.selected_index
            label = f"> {mode.value} <" if is_selected else mode.value
            if not mode.is_available:
                color = "gray40"
            else:
                color = "yellow" if is_selected else "white"
            self.draw_text(screen, label, (center_x, 50 + index * 14), color)