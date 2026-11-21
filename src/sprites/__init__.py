import pygame as pg

vec = pg.math.Vector2

# expose the classes to other modules
from src.sprites.billboard import Billboard
from src.sprites.kart import Kart, get_kart_frame
from src.sprites.ai_kart import AI_Kart
from src.sprites.player import Player
from src.sprites.oil_spill import OilSpill
from src.sprites.traffic_light import TrafficLight
from src.sprites.helicopter import Helicopter