from enum import Enum


class GameMode(Enum):
    GRAND_PRIX = "Grand Prix"
    SINGLE_RACE = "Single Race"
    TIME_TRIAL = "Time Trial"

    @property
    def is_available(self):
        return self != GameMode.GRAND_PRIX  # TODO grand prix not implemented yet

    @property
    def has_opponents(self):
        return self != GameMode.TIME_TRIAL

    @property
    def has_items(self):
        return self != GameMode.TIME_TRIAL