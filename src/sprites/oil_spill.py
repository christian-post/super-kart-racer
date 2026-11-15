import pygame as pg

from src.sprites.kart import Kart

vec = pg.math.Vector2


class OilSpill(pg.sprite.Sprite):
    # floor decal dropped behind a kart, slows the first kart that touches it

    def __init__(self, game, dropping_kart):
        super().__init__(game.all_sprites)
        self.game = game
        self.world_width = game.config["Gameplay.oil_world_width"]
        self.time_left = game.config["Gameplay.oil_lifetime"]

        # drop under the player
        self.map_pos = vec(dropping_kart.map_pos)
        self.dropping_kart = dropping_kart  # immune until it has left the spill

        # trim transparent edges, the floor texture has 1 px per world unit
        sprite = game.assets["sprites"]["oil"]
        visible_part = sprite.subsurface(sprite.get_bounding_rect())
        decal_image = pg.transform.scale(visible_part, (self.world_width, self.world_width))
        self.decal = game.map.add_decal(decal_image, self.map_pos)


    def contact_distance(self, kart):
        return (self.world_width + kart.world_width) / 2


    def update(self, dt):
        self.time_left -= dt
        if self.time_left <= 0:
            self.kill()
            return
        for sprite in self.game.billboards:
            if not isinstance(sprite, Kart):
                continue
            in_contact = self.map_pos.distance_to(sprite.map_pos) < self.contact_distance(sprite)
            if sprite is self.dropping_kart:
                if not in_contact:
                    self.dropping_kart = None
                continue
            if in_contact:
                sprite.apply_effect("oil")
                self.kill()
                return


    def kill(self):
        self.game.map.remove_decal(self.decal)
        super().kill()


    def draw(self, screen):
        pass  # part of the floor, drawn by Mode7
