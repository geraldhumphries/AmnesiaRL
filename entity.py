#!usr/bin/python

# filename entity.py
# pyhack entity module
# contains several classes used to generate entities
# author Gerald Humphries
# course name Advanced Languages
# course number CST8333
# last modified 2013-11-25

import libtcodpy as libtcod
import math


# entities are the player, objects, items and enemies
class Entity:
    """
    Purpose: class that entity objects inherit from
    Student Name: Gerald Humphries
    """
    def __init__(self, x, y, char, color, blocks_movement, con, game):
        """
        Purpose: constructor for class Entity
        Inputs to Function:  x, y, char, color, blocks_movement, con, game
        Outputs from Function: no return value
        Student Name: Gerald Humphries
        """
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.con = con
        self.game = game
        self.blocks_movement = blocks_movement

    def move(self, dx, dy, tiles):
        """
        Purpose: moves the entity after checking if the space is walkable
        Inputs to Function: dx, dy, tiles
        Outputs from Function: has_moved
        Student Name: Gerald Humphries
        """
        has_moved = False
        if tiles[self.x + dx][self.y + dy].is_walkable and self.check_is_walkable(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy
            has_moved = True
        return has_moved

    def check_is_walkable(self, x, y):
        """
        Purpose: checks if a space is walkable
        Inputs to Function: x, y
        Outputs from Function: blocks_movement or True
        Student Name: Gerald Humphries
        """
        for entity in self.game.entities:
            if entity.x == x and entity.y == y:
                return not entity.blocks_movement
        return True

    def draw(self, fov_map):
        """
        Purpose: draws the entity on the map
        Inputs to Function: fov_map
        Outputs from Function: no return value
        Student Name: Gerald Humphries
        """
        if libtcod.map_is_in_fov(fov_map, self.x, self.y):
            libtcod.console_set_default_foreground(self.con, self.color)
            libtcod.console_put_char(self.con, self.x, self.y, self.char, libtcod.BKGND_NONE)

    def clear(self):
        """
        Purpose: clears the entity from the map
        Inputs to Function: no parameters
        Outputs from Function: no return value
        Student Name: Gerald Humphries
        """
        libtcod.console_put_char(self.con, self.x, self.y, ' ', libtcod.BKGND_NONE)

    def tile_distance(self, x, y):
        """
        Purpose: calculate the distance between the entity and a given location
        Inputs to Function: x, y
        Outputs from Function: distance
        Student Name: Gerald Humphries
        """
        distance = math.fabs(self.x - x) + math.fabs(self.y - y)
        return distance


class NextAction:
    """
    Purpose: Acts as an enumerator for the possible actions a player can take
    Student Name: Gerald Humphries
    """
    open = 0  # open a door
    close = 1  # close a door
    pick_up = 2  # pick up an item
    descend = 4  # descend a floor


class Player(Entity):
    """
    Purpose: handles player stats and actions
    Student Name: Gerald Humphries
    """
    def __init__(self, x, y, char, color, con, game):
        """
        Purpose: constructor for class Player
        Inputs to Function: x, y, char, color, con, game
        Outputs from Function: no return value
        Student Name: Gerald Humphries
        """
        Entity.__init__(self, x, y, char, color, True, con, game)

        # player stats
        self.sanity = 100.0  # sanity in %
        self.health = 100  # health in %
        self.fuel = 50.0  # oil lamp fuel in %

        # lamp and sight
        self.BASE_SIGHT_RANGE = 2
        self.lamp_range = 5  # oil lamp range, decreases as fuel gets low
        self.sight_range = self.BASE_SIGHT_RANGE + self.lamp_range  # current sight range
        self.is_lamp_on = True
        self.visibility = 15  # how far the monster can see the player from

        # actions
        self.performing_action = False
        self.next_action = -1

    def toggle_lamp(self, is_lamp_on=None):
        """
        Purpose: toggles the player's lamp on or off
        Inputs to Function: is_lamp_on
        Outputs from Function: no return value
        Student Name: Gerald Humphries
        """
        if is_lamp_on is None:
            if self.is_lamp_on:
                self.is_lamp_on = False
            elif not is_lamp_on:
                self.is_lamp_on = True
        elif is_lamp_on:
            self.is_lamp_on = True
        else:
            self.is_lamp_on = False

    def perform_action(self, x, y):
        """
        Purpose: performs an action specified by the next_action enum
        Inputs to Function:  x, y
        Outputs from Function: no return value
        Student Name: Gerald Humphries
        """
        self.performing_action = False
        if self.next_action == NextAction.open:
            for entity in self.game.entities:
                if entity.char == "+" and self.x + x == entity.x and self.y + y == entity.y:
                    entity.open()
                    return
        elif self.next_action == NextAction.close:
            for entity in self.game.entities:
                if entity.char == "-" and self.x + x == entity.x and self.y + y == entity.y:
                    entity.close()
                    return
        elif self.next_action == NextAction.pick_up:
            for entity in self.game.entities:
                if entity.char == "*" and self.x + x == entity.x and self.y + y == entity.y:
                    self.fuel += entity.collect()
                    return
        elif self.next_action == NextAction.descend:
            for entity in self.game.entities:
                if entity.char == "S" and self.x + x == entity.x and self.y + y == entity.y:
                    entity.descend()
                    return

    def update(self):
        """
        Purpose: performs calculations that happen to the player as time goes on
        Inputs to Function: no parameters
        Outputs from Function: no return value
        Student Name: Gerald Humphries
        """
        if self.is_lamp_on and self.fuel >= 0:
            if self.game.turn_based:
                self.fuel -= 0.2
            else:
                self.fuel -= 0.01

            if 60 <= self.fuel <= 100:
                self.lamp_range = 5
            elif 40 <= self.fuel < 60:
                self.lamp_range = 4
            elif 20 <= self.fuel < 40:
                self.lamp_range = 3
            elif 0 <= self.fuel < 20:
                self.lamp_range = 2
            elif self.fuel <= 0:
                self.lamp_range = 0
            self.visibility = 15
            self.sight_range = self.BASE_SIGHT_RANGE + self.lamp_range
        else:
            self.sight_range = self.BASE_SIGHT_RANGE
            if self.game.turn_based:
                self.sanity -= 1
            else:
                self.sanity -= 0.1

            if 60 <= self.sanity <= 100:
                self.visibility = 1
            elif 30 <= self.sanity < 60:
                self.visibility = 2
            elif 0 <= self.sanity < 30:
                self.visibility = 3


class Monster(Entity):
    """
    Purpose: Class for the Monster
    Student Name: Gerald Humphries
    """
    def __init__(self, x, y, char, color, con, game, level, player):
        """
        Purpose: constructor for class Monster
        Inputs to Function:  x, y, char, color, con, game, level, player
        Outputs from Function: no return value
        Student Name: Gerald Humphries
        """
        Entity.__init__(self, x, y, char, color, True, con, game)
        # spawning and timing
        self.is_spawned = False
        self.SPAWN_DISTANCE = 15
        self.monster_timer = libtcod.random_get_int(0, 30, 30)
        self.monster_index = 0
        self.move_index = 0

        # moving
        self.move_speed = 8  # in frames, lower is faster

        # player
        self.player = player
        self.can_see_player = False

        # level
        self.level = level
        self.fov_map = level.fov_map
        self.path = libtcod.path_new_using_map(self.fov_map, 0.0)

    def spawn(self, player, tiles):
        """
        Purpose: spawns the monster in a random valid tile close to the player
        Inputs to Function: player, tiles
        Outputs from Function: no return value
        Student Name: Gerald Humphries
        """
        valid_spawns = []
        for dx in range(0 - self.SPAWN_DISTANCE, self.SPAWN_DISTANCE):
            dy = self.SPAWN_DISTANCE - math.fabs(dx)
            x = int(dx + player.x)
            y = int(dy + player.y)

            if 0 <= x < len(tiles) and 0 <= y < len(tiles[0]) and tiles[x][y].is_walkable:
                valid_spawns.append(tiles[x][y])

            y = int((0 - dy) + player.y)
            if 0 <= x < len(tiles) and 0 <= y < len(tiles[0]) and tiles[x][y].is_walkable:
                valid_spawns.append(tiles[x][y])

        if len(valid_spawns):
            spawn_tile = valid_spawns[libtcod.random_get_int(0, 0, len(valid_spawns) - 1)]
            self.x = spawn_tile.x
            self.y = spawn_tile.y
            self.is_spawned = True
            libtcod.path_compute(self.path, self.x, self.y, player.x, player.y)

    def despawn(self):
        """
        Purpose: despawns the monster
        Inputs to Function: no parameters
        Outputs from Function: no return value
        Student Name: Gerald Humphries
        """
        self.is_spawned = False
        self.x = None
        self.y = None

    def check_see_player(self):
        """
        Purpose: checks if the monster can see the player. if so, set the path to the player.
        if not, set can_see_player false and slow down
        Inputs to Function: no parameters
        Outputs from Function: can_see_player
        Student Name: Gerald Humphries
        """
        self.compute_monster_fov()
        if (self.can_see_player and self.player.is_lamp_on) or \
                libtcod.map_is_in_fov(self.fov_map, self.player.x, self.player.y):
            self.move_speed = 5
            libtcod.path_compute(self.path, self.x, self.y, self.player.x, self.player.y)
            self.can_see_player = True
        elif libtcod.path_is_empty(self.path):
            self.move_speed = 8
            self.can_see_player = False

        return self.can_see_player

    def compute_monster_fov(self):
        """
        Purpose: computes the monster's fov
        Inputs to Function: no parameters
        Outputs from Function: no return value
        Student Name: Gerald Humphries
        """
    # compute fov of an entity
        libtcod.map_compute_fov(self.fov_map,
                                self.x,
                                self.y,
                                self.player.visibility + self.game.floor,
                                True,
                                libtcod.FOV_RESTRICTIVE)

    def monster_action(self):
        """
        Purpose: performs an action depending on the context
        can attack the player, move, or bash down a door
        Inputs to Function: no parameters
        Outputs from Function: no return value
        Student Name: Gerald Humphries
        """
        if libtcod.path_is_empty(self.path):
            ox, oy = self.level.rooms[libtcod.random_get_int(0, 0, len(self.level.rooms) - 1)].center()
            libtcod.path_compute(self.path, self.x, self.y, ox, oy)
        else:
            x, y = libtcod.path_get(self.path, 0)
            if self.player.x == x and self.player.y == y:
                self.player.health -= 10
            else:
                can_move = True
                for entity in self.game.entities:
                    if x == entity.x and y == entity.y and entity.char == "+":
                        entity.bash()
                        can_move = False
                if can_move:
                    x, y = libtcod.path_walk(self.path, True)
                    dx = x - self.x
                    dy = y - self.y
                    self.move(dx, dy, self.level.tiles)

    def draw(self, fov_map):
        """
        Purpose: draws the monster on the map if spawned
        Inputs to Function: fov_map
        Outputs from Function: no return value
        Student Name: Gerald Humphries
        """
        if self.is_spawned and libtcod.map_is_in_fov(self.fov_map, self.x, self.y):
            libtcod.console_set_default_foreground(self.con, self.color)
            libtcod.console_put_char(self.con, self.x, self.y, self.char, libtcod.BKGND_NONE)

    def update(self):
        """
        Purpose: performs calculations that happen as time goes on
        Inputs to Function: no parameters
        Outputs from Function: is_spawned
        Student Name: Gerald Humphries
        """
        self.move_index += 1
        self.monster_index += 1

        if self.is_spawned and not self.check_see_player() and \
                self.tile_distance(self.player.x, self.player.y) > 15 and self.monster_index > 250:
            self.despawn()
            self.monster_index = 0
            self.monster_timer = libtcod.random_get_int(0, 50, 100)

        elif self.monster_index > self.monster_timer and not self.is_spawned:
            self.monster_index = 0
            self.monster_timer = self.move_speed
            self.spawn(self.player, self.level.tiles)

        elif self.move_index > self.move_speed and self.is_spawned:
            self.move_index = 0
            self.monster_action()

        return self.is_spawned


class Door(Entity):
    """
    Purpose: class for object that represents a door
    Student Name: Gerald Humphries
    """
    def __init__(self, x, y, char, color, con, entities, level, is_open=False):
        """
        Purpose: constructor for class Door
        Inputs to Function: x, y, char, color, con, entities, level, is_open=False
        Outputs from Function: no return value
        Student Name: Gerald Humphries
        """
        Entity.__init__(self, x, y, char, color, True, con, None)

        self.is_open = is_open
        self.BASE_LOCK_STRENGTH = 3
        self.lock_strength = self.BASE_LOCK_STRENGTH
        self.level = level
        self.level.tiles[x][y].is_transparent = False

    def open(self):
        """
        Purpose: open the door
        Inputs to Function: no parameters
        Outputs from Function: no return value
        Student Name: Gerald Humphries
        """
        self.is_open = True
        self.blocks_movement = False
        self.char = "-"
        self.level.tiles[self.x][self.y].is_transparent = True
        self.level.create_fov_maps()

    def close(self):
        """
        Purpose: close the door
        Inputs to Function: no parameters
        Outputs from Function: no return value
        Student Name: Gerald Humphries
        """
        self.is_open = False
        self.blocks_movement = True
        self.char = "+"
        self.lock_strength = self.BASE_LOCK_STRENGTH
        self.level.tiles[self.x][self.y].is_transparent = False
        self.level.create_fov_maps()

    def bash(self):
        """
        Purpose: attempts to bash the door down
        Inputs to Function: no parameters
        Outputs from Function: no return value
        Student Name: Gerald Humphries
        """
        self.lock_strength -= 1
        if self.lock_strength <= 0:
            self.open()


class Fuel(Entity):
    """
    Purpose: Class that represents a unit of lantern fuel in game
    Student Name: Gerald Humphries
    """
    def __init__(self, x, y, char, color, con, entities, level):
        """
        Purpose: constructor for class Fuel
        Inputs to Function: x, y, char, color, con, entities, level
        Outputs from Function: no return value
        Student Name: Gerald Humphries
        """
        Entity.__init__(self, x, y, char, color, False, con, None)

    def collect(self):
        """
        Purpose: to pick up the fuel, removes it from the map and returns the amount of fuel it was worth
        Inputs to Function: no parameters
        Outputs from Function: no return value
        Student Name: Gerald Humphries
        """
        self.x = None
        self.y = None
        return 10


class Stairs(Entity):
    """
    Purpose: Class that represents a staircase
    Student Name: Gerald Humphries
    """
    def __init__(self, x, y, char, color, con, game):
        """
        Purpose: constructor for class Stairs
        Inputs to Function: x, y, char, color, con, game
        Outputs from Function: no return value
        Student Name: Gerald Humphries
        """
        Entity.__init__(self, x, y, char, color, False, con, None)
        self.game = game

    def descend(self):
        """
        Purpose: descend the staircase to the next floor
        Inputs to Function: no parameters
        Outputs from Function: no return value
        Student Name: Gerald Humphries
        """
        self.game.descend_floor()

