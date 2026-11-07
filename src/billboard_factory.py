from src.sprites import Billboard
import src.items  # modules with Billboard subclasses register on import


def create_billboard(game, tiled_object):
    billboard_class = Billboard.subclasses_by_tiled_name.get(tiled_object.name, Billboard)
    return billboard_class(game, tiled_object)