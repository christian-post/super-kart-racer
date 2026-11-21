import pygame as pg
from math import sin, cos, atan2
from random import uniform

from src.sprites.kart import Kart, Direction, MAX_STEER_FRAMES, STEER_FRAME_ANGLE
from src.sprites.helicopter import Helicopter
from src.particle import Particle

vec = pg.math.Vector2



class Player(Kart):
    def __init__(self, game, kart_name):
        pg.sprite.Sprite.__init__(self, game.billboards)
        self.game = game
        self.name = "player"
        self.effect_timers = {}  # same as in PathFollower.__init__
        self.depth = 0
        self.visible = True

        self.angle = -1.54  # TODO should depend on teh track's starting line orientation
        self.acc = vec()
        self.vel = vec()
        self.pos = vec(2892.8, 1216.0)  # fallback if course has no start positions
        self.friction = self.game.config["Gameplay.friction"]
        top_speed = self.game.config["Gameplay.player_top_speed"]
        self.speed = top_speed * (1 - self.friction) / self.friction
        self.last_road_pos = vec(0, 0)  # last known position on road
        
        self.set_sheet(kart_name)  # base_image = current unscaled frame
        self.steer_yaw = 0.0  # visual turn from steering in rad, positive = right
        self.image = self.base_image
        self.rect = self.image.get_rect()
        self.rect.topleft = (84, 84)
        
        self.time_passed = 0 # seconds from the start of the game
        self.steer_time = 0 # seconds the player is pressing a direction
        self.lastdir: Direction = Direction.LEFT
        self.moving = 1 # 1 forward, -1 backwards
        self.dust_timer = 0
        self.dirt_timer = 0
        self.fire_timer = 0

        self.item = None  # held item
        self.helicopter = None  # set while being carried back to the road
        
    
    def update(self, dt):
        self.time_passed += dt
        self.update_effects(dt)
        self.update_sheet_animation(dt)
        if "turbo" in self.effect_timers or "maxturbo" in self.effect_timers:
            self.emit_turbo_fire(dt)
        keys = pg.key.get_pressed()
        
        if not self.game.started:
            if keys[pg.K_w]:
                self.dust_timer += dt
                if self.dust_timer >= 0.3:
                    # create two particles (left and right)
                    Particle(
                        self.game, 
                        self.rect.bottomright, 
                        images=[self.game.assets["sprites"]["cloud"]],
                        colors=[pg.Color('white')],
                        vel=vec(1, 0),
                        random_angle=20,
                        vanish_speed=20,
                        end_size=1.4
                        )
                    Particle(
                        self.game, 
                        self.rect.bottomleft, 
                        images=[self.game.assets["sprites"]["cloud"]],
                        colors=[pg.Color('white')],
                        vel=vec(-1, 0),
                        random_angle=20,
                        vanish_speed=20,
                        end_size=1.4
                        )
                    self.dust_timer = 0
            
        elif not self.is_rescued:
            if self.moving == 1:
                turn_force = 0.00625 # how much the angle changes when turning
            else:
                turn_force = 0.015625
            steer_anim_speed = 10 # turning animation speed
            
            current_speed = self.vel.length()
            
            # steer
            steer_frames = min(MAX_STEER_FRAMES - 1, int(self.steer_time * steer_anim_speed))

            if keys[pg.K_a]:
                # turning left
                if self.lastdir == Direction.RIGHT:
                    self.steer_time = 0
                self.steer_time += dt
                self.angle -= turn_force * dt * current_speed * self.moving
                steer_frames += 1  # first turning frame right away
                self.lastdir = Direction.LEFT
            elif keys[pg.K_d]:
                # turning right
                if self.lastdir == Direction.LEFT:
                    self.steer_time = 0
                self.steer_time += dt
                self.angle += turn_force * dt * current_speed * self.moving
                steer_frames += 1
                self.lastdir = Direction.RIGHT
            else:
                self.steer_time -= dt

            # reversing turns the kart the other way
            steer_sign = 1 if self.lastdir == Direction.RIGHT else -1
            self.steer_yaw = steer_sign * self.moving * steer_frames * STEER_FRAME_ANGLE
            
            # limit the steer time between 0 and the maximum image index
            self.steer_time = max(min(self.steer_time, 0.6), 0)
                
            # move forward or backwards
            if keys[pg.K_w]:
                self.moving = 1
                self.acc.x = self.speed
                self.acc.y = self.speed
            elif keys[pg.K_s]:
                self.moving = -1
                self.acc.x = self.speed * -0.4
                self.acc.y = self.speed * -0.4

            # ground tiles affect acceleration
            ground_speed = self.game.ground_speed_at(self.pos)
            if ground_speed == 1.0:
                # store position if ground_speed is 1 (= on road)
                self.last_road_pos.x = self.pos.x
                self.last_road_pos.y = self.pos.y

            # turbos cancel the ground effect to some extent
            # TODO put this in config
            if "turbo" in self.effect_timers or "maxturbo" in self.effect_timers:
                ground_speed = max(1.0, ground_speed + 0.5)

            self.acc *= ground_speed * self.speed_factor
    
            self.vel.x += self.acc.x * cos(self.angle) * dt
            self.vel.y += self.acc.y * sin(self.angle) * dt
            self.pos += self.vel * dt
            
            self.acc *= 0
            # apply friction
            self.vel *= self.friction

            # self.game.debug_values['velocity'] = f'{self.vel.length():.2f}'
            
            # jiggle texture up and down
            if int(self.time_passed * self.game.config["Visuals.kart_jiggle_speed"]) % 2 == 0 and current_speed >= 32:
                self.rect.top = 85
            else:
                self.rect.top = 84
            
            # create dust clouds when steering
            self.dust_timer += dt
            if self.dust_timer >= 0.2:
                if self.lastdir == Direction.RIGHT:
                    v = vec(3, 0) * self.moving
                elif self.lastdir == Direction.LEFT:
                    v = vec(-3, 0) * self.moving
                if self.steer_time >= 0.3 and current_speed > 128:
                    if self.moving == 1:
                        p = Particle(
                            self.game, 
                            self.rect.midbottom, 
                            images=[self.game.assets["sprites"]["cloud"]],
                            colors=[pg.Color('white')],
                            vel=v,
                            random_angle=30,
                            vanish_speed=20,
                            end_size=1.4
                            )
                        p.add_force(vec(0, 1), 10)
                    else:
                        p = Particle(
                            self.game, 
                            self.rect.midbottom, 
                            images=[self.game.assets["sprites"]["cloud"]],
                            colors=[pg.Color('white')],
                            vel=v, 
                            random_angle=30,
                            vanish_speed=20,
                            end_size=0.9
                            )
                        p.add_force(vec(0, -2), 10)
                    
                self.dust_timer = 0


            # create dirt/grass particles when offroad
            if ground_speed < 1.0:
                # TODO check for different ground tiles
                if self.vel.length_squared() > 0.0001:
                    self.dirt_timer += dt
                if self.dirt_timer >= 0.2:
                    self.dirt_timer = 0
                    # create two particles (left and right)
                    Particle(
                        self.game, 
                        self.rect.bottomright, 
                        images=[self.game.assets["sprites"]["dirt"]],
                        colors=[pg.Color('white')],
                        vel=vec(1, 0),
                        random_angle=20,
                        vanish_speed=20,
                        end_size=1.4
                        )
                    Particle(
                        self.game, 
                        self.rect.bottomleft, 
                        images=[self.game.assets["sprites"]["dirt"]],
                        colors=[pg.Color('white')],
                        vel=vec(-1, 0),
                        random_angle=20,
                        vanish_speed=20,
                        end_size=1.4
                        )

        # check against the killzone
        if not self.is_rescued and self.game.check_in_killzone(self.pos):
            # helicopter carries the kart back to the last road position
            drop_pos, drop_angle = self.find_drop_position()
            self.helicopter = Helicopter(self.game, self, drop_pos, drop_angle)


    def find_drop_position(self):
        # nearest point on the AI path, facing along it
        course = self.game.course
        nearest = course.nearest_path_point(self.last_road_pos) if course else None
        if nearest is None:
            return vec(self.last_road_pos), self.angle
        point, direction = nearest
        return point, atan2(direction.y, direction.x)


    @property
    def is_rescued(self):
        return self.helicopter is not None


    def emit_turbo_fire(self, dt):
        config = self.game.config
        interval = config["Visuals.fire_particle_interval"]
        speed = config["Visuals.fire_particle_speed"]
        self.fire_timer += dt
        while self.fire_timer >= interval:
            self.fire_timer -= interval
            # particles move down on screen = toward the camera
            Particle(
                self.game,
                self.rect.midbottom - vec(0, 4),
                colors=[pg.Color("white")],
                vel=vec(uniform(-0.5, 0.5) * speed, speed),
                vanish_speed=0,  # animation decides the lifetime
                animation_frames=self.game.assets["spritesheets"]["fire"],
                frame_duration=config["Visuals.fire_frame_duration"],
            )


    @property
    def map_pos(self):
        return self.pos
