# TODO grab and populate the SCENES dict automatically
from src.scenes.title_screen import TitleScreen
from src.scenes.asset_loader import AssetLoader
from src.scenes.course_select import CourseSelect
from src.scenes.kart_select import KartSelect
from src.scenes.mode_select import ModeSelect
from src.scenes.race import Race
from src.scenes.grand_prix_results import GrandPrixResults

SCENES = {
    "AssetLoader": AssetLoader,
    "TitleScreen": TitleScreen,
    "CourseSelect": CourseSelect,
    "KartSelect": KartSelect,
    "ModeSelect": ModeSelect,
    "Race": Race,
    "GrandPrixResults": GrandPrixResults
}