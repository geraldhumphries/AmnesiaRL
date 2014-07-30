# !usr/bin/python

from lib import libtcodpy as libtcod


class Noise:
    def __init__(self, x, y, volume, con, game):
        self.x = x
        self.y = y
        self.volume = volume
        self.con = con
        self.game = game

    def set_volume(self, volume):
        self.volume = volume
        if self.volume > 100:
            self.volume = 100

    def update(self):
        if self.game.turn_based:
            self.volume -= 25
        else:
            self.volume -= 3


class Light:
    def __init__(self, brightness, con, game):
        self.brightness = brightness
        self.con = con
        self.game = game
        self.fov_map = libtcod.map_new(game.level.width, game.level.height)

    def calculate_tile_brightness(self, tiles, x, y, top_left, bottom_right):
        if self.brightness > 0:
            libtcod.map_compute_fov(self.fov_map, x, y, self.brightness, True, libtcod.FOV_SHADOW)
            for iy in range(top_left[1], bottom_right[1]):
                for ix in range(top_left[0], bottom_right[0]):
                    if libtcod.map_is_in_fov(self.fov_map, ix, iy):
                        tiles[x][y].brightness = self.brightness - tiles[x][y].distance_to(x, y)



class Fov:
    def __init__(self, fov_map, entity, level, con, game):
        self.con = con
        self.game = game
        self.fov_map = fov_map
        self.level = level
        self.entity = entity
        self.create(fov_map, level)

    @staticmethod
    def create(fov_map, level):
        for y in range(level.height):
            for x in range(level.width):
                libtcod.map_set_properties(fov_map, x, y,
                                           level.tiles[x][y].is_transparent,
                                           level.tiles[x][y].is_walkable)

    def compute(self):
        # compute fov of an entity
        libtcod.map_compute_fov(self.fov_map,
                                self.entity.x,
                                self.entity.y,
                                self.entity.sight_range,
                                True,
                                libtcod.FOV_RESTRICTIVE)