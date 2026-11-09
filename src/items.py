from random import choices

from src.sprites import Billboard, OilSpill, Kart


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


class Shrink(Item):
    name = "shrink"

    def use(self, game, kart):
        # every kart except the user
        for sprite in game.billboards:
            if isinstance(sprite, Kart) and sprite is not kart:
                sprite.apply_effect("shrink")


ITEM_TYPES = {item.name: item for item in (Turbo, Maxturbo, Oil, Shrink)}


def random_item(game, position, kart_count):
    # position 1 = first; maps relative race position onto the ItemOdds columns
    odds = game.config["ItemOdds"]
    names = list(odds.keys())
    column_count = len(odds[names[0]])
    relative_position = (position - 1) / max(1, kart_count - 1)
    column = round(relative_position * (column_count - 1))
    weights = [odds[name][column] for name in names]
    name = choices(names, weights=weights)[0]
    return ITEM_TYPES[name]()


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
            standings = self.game.scene_stack[-1].standings  # TODO refactor to not access scene directly
            position = standings.position_of(kart)
            kart.item = random_item(self.game, position, len(standings.karts))
        self.time_until_respawn = self.respawn_time


    def update(self, dt):
        super().update(dt)
        if not self.active:
            self.time_until_respawn -= dt
            return
        for sprite in self.game.billboards:
            if isinstance(sprite, Kart) and self.touches(sprite):
                self.collect(sprite)
                return


    def project(self):
        super().project()
        if not self.active:
            self.visible = False