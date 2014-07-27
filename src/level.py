# !usr/bin/python

from lib import libtcodpy as libtcod
from src.entity import Door, Closet
from src.entity import Fuel
from src.entity import Stairs


class Level:
    ROOM_MAX_SIZE = 10
    ROOM_MIN_SIZE = 4
    MAX_ROOMS = 30

    def __init__(self, width, height, con):
        self.width = width
        self.height = height
        self.con = con

        # tile colors
        self.color_lit_floor = libtcod.Color(100, 100, 100)
        self.color_lit_wall = libtcod.Color(255, 255, 255)
        self.color_unlit_floor = libtcod.Color(50, 50, 50)
        self.color_unlit_wall = libtcod.Color(50, 50, 50)

        # fov map object
        self.fov_map = libtcod.map_new(self.width, self.height)
        self.monster_fov = libtcod.map_new(self.width, self.height)

        # room list
        self.rooms = []

        # tile list
        self.tiles = [[Tile(False, x, y)
                       for y in range(self.height)]
                      for x in range(self.width)]
        
        # screen
        self.top_left = [0, 0]
        self.bottom_right = [0, 0]

    def create_map(self, player, game):
        number_of_rooms = 0

        for r in range(self.MAX_ROOMS):
            # generate random dimensions
            w = libtcod.random_get_int(0, self.ROOM_MIN_SIZE, self.ROOM_MAX_SIZE)
            h = libtcod.random_get_int(0, self.ROOM_MIN_SIZE, self.ROOM_MAX_SIZE)
            x = libtcod.random_get_int(0, 0, self.width - w - 1)
            y = libtcod.random_get_int(0, 0, self.height - h - 1)

            new_room = Room(x, y, w, h)

            # check if room overlaps another
            is_valid = True
            for existing_room in self.rooms:
                if new_room.intersect(existing_room):
                    is_valid = False
                    break

            if is_valid:
                self.create_room(new_room)
                (new_room_x, new_room_y) = new_room.center()

                if number_of_rooms == 0:
                    # first room, place the player here
                    player.x = new_room_x
                    player.y = new_room_y

                else:
                    # get a random existing room to run a hallway to
                    (existing_x, existing_y) = self.rooms[libtcod.random_get_int(0, 0, number_of_rooms - 1)].center()
                    self.create_tunnel(new_room_x, new_room_y, existing_x, existing_y)

                number_of_rooms += 1
                self.rooms.append(new_room)

        # add doors
        for room in self.rooms:
            self.add_doors(room, game.entities)
            self.add_closets(room, game.entities)

        self.add_items(game.entities)
        self.add_stairs(game)

        # create fov map
        self.create_fov_maps()

    def create_fov_maps(self):
        for y in range(self.height):
            for x in range(self.width):
                libtcod.map_set_properties(self.fov_map, x, y,
                                           self.tiles[x][y].is_transparent,
                                           self.tiles[x][y].is_walkable)
                libtcod.map_set_properties(self.monster_fov, x, y,
                                           self.tiles[x][y].is_walkable,  # monster can see through doors
                                           self.tiles[x][y].is_walkable)

    def create_room(self, room):
        # sets the "wall" tiles of a room to be "floor" tiles
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.tiles[x][y].is_walkable = True
                self.tiles[x][y].is_transparent = True

    def create_tunnel(self, start_x, start_y, end_x, end_y):
        # create a path from one point to another
        x_length = end_x - start_x
        y_length = end_y - start_y

        if x_length >= y_length:
            for x in range(min(start_x, start_x + x_length), max(start_x, start_x + x_length) + 1):
                self.tiles[x][start_y].is_walkable = True
                self.tiles[x][start_y].is_transparent = True

            for y in range(min(start_y, start_y + y_length), max(start_y, start_y + y_length) + 1):
                self.tiles[end_x][y].is_walkable = True
                self.tiles[end_x][y].is_transparent = True

        if y_length > x_length:
            for y in range(min(start_y, start_y + y_length), max(start_y, start_y + y_length) + 1):
                self.tiles[start_x][y].is_walkable = True
                self.tiles[start_x][y].is_transparent = True

            for x in range(min(start_x, start_x + x_length), max(start_x, start_x + x_length) + 1):
                self.tiles[x][end_y].is_walkable = True
                self.tiles[x][end_y].is_transparent = True

    def add_doors(self, room, entities):
        for x in range(room.x1, room.x2):
            # top edge
            if self.tiles[x][room.y1].is_walkable and self.num_adjacent_floors(x, room.y1) <= 2:
                entities.append(Door(x, room.y1, "+", libtcod.light_gray, self.con, entities, self))

            # bottom edge
            if self.tiles[x][room.y2].is_walkable and self.num_adjacent_floors(x, room.y2) <= 2:
                entities.append(Door(x, room.y2, "+", libtcod.light_gray, self.con, entities, self))

        for y in range(room.y1, room.y2):
            # left edge
            if self.tiles[room.x1][y].is_walkable and self.num_adjacent_floors(room.x1, y) <= 2:
                entities.append(Door(room.x1, y, "+", libtcod.light_gray, self.con, entities, self))

            # right edge
            if self.tiles[room.x2][y].is_walkable and self.num_adjacent_floors(room.x2, y) <= 2:
                entities.append(Door(room.x2, y, "+", libtcod.light_gray, self.con, entities, self))

    def num_adjacent_floors(self, x, y):
        adjacent_floors = 0
        if self.tiles[x + 1][y].is_walkable:
            adjacent_floors += 1
        if self.tiles[x][y + 1].is_walkable:
            adjacent_floors += 1
        if self.tiles[x - 1][y].is_walkable:
            adjacent_floors += 1
        if self.tiles[x][y - 1].is_walkable:
            adjacent_floors += 1

        return adjacent_floors

    def add_closets(self, room, entities):
        odds = 50  # 1 in [odds] chance that a closet will spawn for every tile adjacent to a wall in a room
        for x in range(room.x1, room.x2):

            # top edge
            if self.tiles[x][room.y1 + 1].is_walkable and self.will_spawn(odds):
                entities.append(Closet(x, room.y1 + 1, self.con))

            # bottom edge
            if self.tiles[x][room.y2 - 1].is_walkable and self.will_spawn(odds):
                entities.append(Closet(x, room.y2 - 1, self.con))

        for y in range(room.y1, room.y2):
            # left edge
            if self.tiles[room.x1 + 1][y].is_walkable and self.will_spawn(odds):
                entities.append(Closet(room.x1 + 1, y, self.con))

            # right edge
            if self.tiles[room.x2 - 1][y].is_walkable and self.will_spawn(odds):
                entities.append(Closet(room.x2 - 1, y, self.con))

    def add_stairs(self, game):
        added = False
        while not added:
            x = libtcod.random_get_int(0, 0, len(self.tiles) - 1)
            y = libtcod.random_get_int(0, 0, len(self.tiles[0]) - 1)
            if self.tiles[x][y].is_walkable:
                game.entities.append(Stairs(x, y, self.con, game))
                added = True

    def add_items(self, entities):
        for i in range(50):
            x = libtcod.random_get_int(0, 0, len(self.tiles) - 1)
            y = libtcod.random_get_int(0, 0, len(self.tiles[0]) - 1)
            if self.tiles[x][y].is_walkable:
                entities.append(Fuel(x, y, self.con))

    def draw(self, player, screen_width, screen_height):
        # compute the player's fov
        self.compute_fov(self.fov_map, player)
        tlx = round(player.x - (screen_width - 1) / 2) - 1
        tly = round(player.y - (screen_height - 1) / 2) - 1
        self.top_left = [round(player.x - (screen_width - 1) / 2) - 1, round(player.y - (screen_height - 1) / 2) - 1]
        brx = round(player.x + (screen_width - 1) / 2)
        bry = round(player.y + (screen_height - 1) / 2)
        self.bottom_right = [round(player.x + (screen_width - 1) / 2), round(player.y + (screen_height - 1) / 2)]

        if self.bottom_right[0] > self.width:
            self.top_left[0] = self.width - screen_width
            self.bottom_right[0] = self.width

        if self.top_left[0] < 0:
            self.top_left[0] = 0
            self.bottom_right[0] = screen_width

        if self.bottom_right[1] > self.height:
            self.top_left[1] = self.height - screen_height
            self.bottom_right[1] = self.height

        if self.top_left[1] < 0:
            self.top_left[1] = 0
            self.bottom_right[1] = screen_height

        x_draw = 0
        y_draw = 0
        # draw the level on the console
        for y in range(self.top_left[1], self.bottom_right[1]):
            for x in range(self.top_left[0], self.bottom_right[0]):
                if libtcod.map_is_in_fov(self.fov_map, x, y) or self.tiles[x][y].is_revealed:
                    self.tiles[x][y].is_revealed = True
                    if libtcod.map_is_in_fov(self.fov_map, x, y):
                        if not self.tiles[x][y].is_walkable:
                            libtcod.console_put_char_ex(self.con, x_draw, y_draw, '#', self.color_lit_wall, libtcod.BKGND_SET)
                        else:
                            # floor
                            libtcod.console_put_char_ex(self.con, x_draw, y_draw, '.', self.color_lit_floor, libtcod.BKGND_SET)
                    else:
                        if not self.tiles[x][y].is_walkable:
                            libtcod.console_put_char_ex(self.con, x_draw, y_draw, '#', self.color_unlit_wall, libtcod.BKGND_SET)
                        else:
                            # floor
                            libtcod.console_put_char_ex(self.con, x_draw, y_draw, '.', self.color_unlit_floor, libtcod.BKGND_SET)
                x_draw += 1
            y_draw += 1
            x_draw = 0

    @staticmethod
    def compute_fov(fov_map, entity):
        # compute fov of an entity
        libtcod.map_compute_fov(fov_map,
                                entity.x,
                                entity.y,
                                entity.sight_range,  # entity's default sight range plus light source
                                True,
                                libtcod.FOV_RESTRICTIVE)

    @staticmethod
    def will_spawn(odds):
        return libtcod.random_get_int(0, 0, odds) == odds


# helps make new rooms
class Room:
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        center_x = round((self.x1 + self.x2) / 2)
        center_y = round((self.y1 + self.y2) / 2)
        return center_x, center_y

    # check if the room intersects with another
    def intersect(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

    def contains_tile(self, x, y):
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2


class Tile:
    # is_walkable means an entity can walk on the tile
    # is_transparent means an entity can see through the tile
    # revealed means the tile has been seen by the player
    def __init__(self, is_walkable, x, y, is_transparent=None, is_revealed=False):
        self.is_walkable = is_walkable
        self.x = x
        self.y = y

        if is_transparent is None:
            is_transparent = is_walkable
        self.is_transparent = is_transparent

        self.is_revealed = is_revealed