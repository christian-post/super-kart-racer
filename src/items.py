from random import choice

from src.sprites import Billboard, Player, OilSpill


class Item:
    # new item: subclass, set name, add to ITEM_TYPES
    # portrait = assets/portraits/item_<name>.png
    name = None

    def use(self, game, kart):
        raise NotImplementedError


class Turbo(Item):
    name = "turbo"

    def use(self, game, kart):
        kart.apply_effect("turbo")


class Maxturbo(Item):
    name = "maxturbo"

    def use(self, game, kart):
        kart.apply_effect("maxturbo")


class Oil(Item):
    name = "oil"

    def use(self, game, kart):
        OilSpill(game, kart)


ITEM_TYPES = [Turbo, Maxturbo, Oil]


def random_item():
    return choice(ITEM_TYPES)()


class ItemBox(Billboard):
    # gives the player a random item on contact, respawns after a delay
    def __init__(self, game, tiled_object):
        super().__init__(game, tiled_object)
        self.respawn_time = game.config["Gameplay.item_box_respawn_time"]
        self.time_until_respawn = 0.0


    @property
    def active(self):
        return self.time_until_respawn <= 0


    def touches(self, kart):
        contact_distance = (self.world_width + kart.world_width) / 2
        return self.map_pos.distance_to(kart.map_pos) < contact_distance


    def collect(self, kart):
        # box breaks either way, item only if the slot is empty
        if kart.item is None:
            kart.item = random_item()
        self.time_until_respawn = self.respawn_time


    def update(self, dt):
        super().update(dt)
        if not self.active:
            self.time_until_respawn -= dt
            return
        for sprite in self.game.billboards:
            if isinstance(sprite, Player) and self.touches(sprite):
                self.collect(sprite)
                return


    def project(self):
        super().project()
        if not self.active:
            self.visible = False