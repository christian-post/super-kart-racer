from pathlib import Path
import pygame as pg

from src.scenes.scene import Scene
from src.game_mode import GameMode
from src.hud import HUD


class CourseSelect(Scene):
    def __init__(self, game, **kwargs):
        super().__init__(game)
        # every .tmx file in the assets folder is a course
        # tmx_files = glob.glob(path.join(game.assets_folder, "courses", "*.tmx"))
        tmx_files = Path(game.assets_folder, "courses").glob("*.tmx")
        self.courses = sorted(f.stem for f in tmx_files)
        self.selected_index = 0


    def get_event(self, event):
        if event.type != pg.KEYDOWN:
            return
        if event.key == pg.K_ESCAPE:
            self.game.switch_scene("ModeSelect")
        elif not self.courses:
            return
        elif event.key in (pg.K_w, pg.K_UP):
            self.selected_index = (self.selected_index - 1) % len(self.courses)
        elif event.key in (pg.K_s, pg.K_DOWN):
            self.selected_index = (self.selected_index + 1) % len(self.courses)
        elif event.key in (pg.K_RETURN, pg.K_SPACE):
            self.game.switch_scene("KartSelect", course_name=self.courses[self.selected_index])


    def draw(self, screen):
        screen.fill(pg.Color("black"))
        center_x = screen.get_width() // 2
        self.draw_text(screen, "SELECT COURSE", (center_x, 20))

        if not self.courses:
            self.draw_text(screen, "No courses found", (center_x, 70), "red")
            return

        for index, course_name in enumerate(self.courses):
            is_selected = index == self.selected_index
            label = f"> {course_name} <" if is_selected else course_name
            color = "yellow" if is_selected else "white"
            self.draw_text(screen, label, (center_x, 50 + index * 14), color)

        if self.game.mode == GameMode.TIME_TRIAL:
            self.draw_best_times(screen, self.courses[self.selected_index])


    def draw_best_times(self, screen, course_name):
        center_x = screen.get_width() // 2
        bottom = screen.get_height() - 10
        race_time = self.game.records.best_time(course_name, "race")
        lap_time = self.game.records.best_time(course_name, "lap")
        race_text = HUD.format_time(race_time) if race_time is not None else "--:--.--"
        lap_text = HUD.format_time(lap_time) if lap_time is not None else "--:--.--"
        self.draw_text(screen, f"BEST {race_text}", (center_x, bottom - 12), "gold")
        self.draw_text(screen, f"LAP  {lap_text}", (center_x, bottom), "gold")