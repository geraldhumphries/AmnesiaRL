# !usr/bin/python

import math
from lib import libtcodpy as libtcod
from src.pathing import Light
from src.pathing import Noise


# entities are the player, objects, items and enemies
class Entity:
    def __init__(self, x, y, char, color, blocks_movement, light, noise, entity_fov_map, con, game):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.con = con
        self.game = game
        self.blocks_movement = blocks_movement
        self.light = light
        self.noise = noise
        self.entity_fov_map = entity_fov_map

    def move(self, dx, dy, tiles):
        has_moved = False
        if tiles[self.x + dx][self.y + dy].is_walkable and self.check_is_walkable(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy
            has_moved = True
        return has_moved

    def check_is_walkable(self, x, y):
        for entity in self.game.entities:
            if entity.x == x and entity.y == y:
                return not entity.blocks_movement
        return True

    def draw(self, fov_map, top_left, bottom_right, tiles):
        if libtcod.map_is_in_fov(fov_map, self.x, self.y) and tiles[self.x][self.y].brightness > 0:
            screen_x, screen_y = self.screen_xy(self, top_left, bottom_right, self.x, self.y)
            libtcod.console_set_default_foreground(self.con, self.color)
            libtcod.console_put_char(self.con, screen_x, screen_y, self.char, libtcod.BKGND_NONE)

    def compute_fov(self, sight_range):
        libtcod.map_compute_fov(self.entity_fov_map,
                                self.x,
                                self.y,
                                sight_range,
                                True,
                                libtcod.FOV_RESTRICTIVE)

    def clear(self):
        libtcod.console_put_char(self.con, self.x, self.y, ' ', libtcod.BKGND_NONE)

    def tile_distance(self, x, y):
        distance = math.fabs(self.x - x) + math.fabs(self.y - y)
        return distance

    @staticmethod
    def screen_xy(self, top_left, bottom_right,  x, y):
        screen_x = x - top_left[0]
        screen_y = y - top_left[1]
        return screen_x, screen_y


class NextAction:
    open = 0  # open a door
    close = 1  # close a door
    enter = 3  # enter a closet
    pick_up = 2  # pick up an item
    descend = 4  # descend a floor
    grab = 5  # grab an entity


class Player(Entity):
    BASE_SIGHT_RANGE = 15
    class_char = '@'
    class_color = libtcod.white

    def __init__(self, x, y, fov_map, con, game):
        Entity.__init__(self, x, y, self.class_char, self.class_color, True,
                        Light(5, fov_map, con, game), Noise(x, y, 1, con, game), fov_map, con, game)

        # player stats
        self.sanity = 100.0  # sanity in %
        self.health = 100  # health in %
        self.stamina = 100.0  # stamina in %
        self.fuel = 50.0  # oil lamp fuel in %

        # lamp and sight
        self.lamp_range = 5  # oil lamp range, decreases as fuel gets low
        self.is_lamp_on = True
        self.sight_range = self.BASE_SIGHT_RANGE

        # actions
        self.performing_action = False
        self.next_action = -1
        self.grabbed_entity = None
        self.is_moving_entity = False
        self.is_sneaking = False

    def toggle_lamp(self, is_lamp_on=None):
        if is_lamp_on is None:
            self.is_lamp_on = not self.is_lamp_on
        else:
            self.is_lamp_on = is_lamp_on
        if self.is_lamp_on:
            self.light.brightness = self.lamp_range
        else:
            self.light.brightness = 1

    def toggle_sneak(self, is_sneaking=None):
        if is_sneaking is None:
            self.is_sneaking = not self.is_sneaking
        else:
            self.is_sneaking = is_sneaking

    def perform_action(self, x, y):
        self.performing_action = False
        if self.next_action == NextAction.open:
            for entity in self.game.entities:
                if entity.char == Door.closed_char and self.x + x == entity.x and self.y + y == entity.y:
                    entity.open()
                    return
        elif self.next_action == NextAction.close:
            for entity in self.game.entities:
                if entity.char == Door.open_char and self.x + x == entity.x and self.y + y == entity.y:
                    entity.close()
                    return
        elif self.next_action == NextAction.pick_up:
            for entity in self.game.entities:
                if entity.char == Fuel.class_char and self.x + x == entity.x and self.y + y == entity.y:
                    self.fuel += entity.collect()
                    return
        elif self.next_action == NextAction.descend:
            for entity in self.game.entities:
                if entity.char == Stairs.class_char and self.x + x == entity.x and self.y + y == entity.y:
                    entity.descend()
                    return
        elif self.next_action == NextAction.grab:
            for entity in self.game.entities:
                if entity.char == Closet.class_char and self.x + x == entity.x and self.y + y == entity.y:
                    self.grab(entity)
                    return

    def grab(self, entity):
        self.grabbed_entity = entity
        self.is_moving_entity = True

    def drop(self):
        self.grabbed_entity = None
        self.is_moving_entity = False

    def move(self, dx, dy, tiles):
        has_moved = False
        if self.stamina >= 5 and tiles[self.x + dx][self.y + dy].is_walkable and \
                self.check_is_walkable(self.x + dx, self.y + dy):
            if self.is_moving_entity:
                if self.stamina >= 15:
                    self.grabbed_entity.x = self.x
                    self.grabbed_entity.y = self.y
                    self.stamina -= 10
                else:
                    self.drop()
            if self.is_sneaking:
                self.stamina -= 5
            self.x += dx
            self.y += dy
            self.stamina -= 5
            has_moved = True
        return has_moved

    def update(self, tiles):
        # fuel
        if self.is_lamp_on and self.fuel >= 0:
            if self.game.turn_based:
                self.fuel -= 0.2
            else:
                self.fuel -= 0.03

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

        # sanity
        if tiles[self.x][self.y].brightness > 2:
            if self.game.turn_based:
                self.sanity += 0.2
            else:
                self.sanity += 0.02
        else:
            if self.game.turn_based:
                self.sanity -= (3 - tiles[self.x][self.y].brightness) / 2
            else:
                self.sanity -= (3 - tiles[self.x][self.y].brightness) / 7

        if self.sanity > 100:
            self.sanity = 100

        # stamina
        if self.game.turn_based:
            self.stamina += 6
        else:
            self.stamina += 0.7

        if self.stamina > 100:
            self.stamina = 100


class Monster(Entity):
    SPAWN_DISTANCE = 12
    class_char = '&'
    class_color = libtcod.red

    def __init__(self, x, y, level, player, fov_map, con, game):
        Entity.__init__(self, x, y, self.class_char, self.class_color, True,
                        Light(0, fov_map, con, game), Noise(x, y, 0, con, game), fov_map, con, game)
        # spawning and timing
        self.is_spawned = False
        self.monster_timer = libtcod.random_get_int(0, 30, 100)
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
        self.is_spawned = False
        self.x = None
        self.y = None

    def check_see_player(self, tiles):
        self.compute_monster_fov()

        if self.game.turn_based or libtcod.map_is_in_fov(self.fov_map, self.player.x, self.player.y) \
                and tiles[self.player.x][self.player.y].brightness > 1:
            self.can_see_player = True
        else:
            self.can_see_player = False

        if self.can_see_player:
            self.move_speed = 5
            libtcod.path_compute(self.path, self.x, self.y, self.player.x, self.player.y)
        else:
            self.move_speed = 8

        if libtcod.path_is_empty(self.path):
            self.move_speed = 8
            self.can_see_player = False

        print(self.can_see_player)

        return self.can_see_player

    def compute_monster_fov(self):
        # compute fov of an entity
        libtcod.map_compute_fov(self.fov_map,
                                self.x,
                                self.y,
                                25,
                                True,
                                libtcod.FOV_RESTRICTIVE)

    def monster_action(self):
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
                    if entity.blocks_movement and x == entity.x and y == entity.y and \
                            (entity.char == Door.closed_char or entity.char == Closet.class_char):
                        entity.bash()
                        can_move = False
                if can_move:
                    x, y = libtcod.path_walk(self.path, True)
                    dx = x - self.x
                    dy = y - self.y
                    self.move(dx, dy, self.level.tiles)

    def draw(self, fov_map, top_left, bottom_right, tiles):
        if self.is_spawned and libtcod.map_is_in_fov(self.fov_map, self.x, self.y) and tiles[self.x][self.y].brightness > 0:
            # set the game to real time when the player sees the monster
            if self.game.turn_based:
                self.game.turn_based = False
            screen_x, screen_y = self.screen_xy(self, top_left, bottom_right, self.x, self.y)
            libtcod.console_set_default_foreground(self.con, self.color)
            libtcod.console_put_char(self.con, screen_x, screen_y, self.char, libtcod.BKGND_NONE)

    def update(self, tiles):
        self.move_index += 1
        self.monster_index += 1

        if self.is_spawned and not self.check_see_player(tiles) and \
                self.tile_distance(self.player.x, self.player.y) > 15 and self.monster_index > 250:
            self.despawn()
            self.monster_index = 0
            self.monster_timer = libtcod.random_get_int(0, 50, 100)

        elif self.monster_index > self.monster_timer and not self.is_spawned:
            self.monster_index = 0
            self.monster_timer = self.move_speed
            self.spawn(self.player, self.level.tiles)

        elif self.is_spawned and not self.game.turn_based and self.move_index > self.move_speed:
            self.move_index = 0
            self.monster_action()

        elif self.is_spawned and self.game.turn_based:
            self.move_index = 0
            self.monster_action()


class Door(Entity):
    BASE_STRENGTH = 5
    closed_char = "+"
    open_char = "-"
    class_color = libtcod.light_gray

    def __init__(self, x, y, level, fov_map, con, game, is_open=False):
        Entity.__init__(self, x, y, self.closed_char, self.class_color, True,
                        Light(0, fov_map, con, game), Noise(x, y, 0, con, None), fov_map, con, game)

        self.is_open = is_open
        self.strength = self.BASE_STRENGTH
        self.level = level
        self.level.tiles[x][y].is_transparent = False

    def open(self):
        self.is_open = True
        self.blocks_movement = False
        self.char = self.open_char
        self.level.tiles[self.x][self.y].is_transparent = True
        self.level.create_fov_maps()

    def close(self):
        self.is_open = False
        self.blocks_movement = True
        self.char = self.closed_char
        self.strength = self.BASE_STRENGTH
        self.level.tiles[self.x][self.y].is_transparent = False
        self.level.create_fov_maps()

    def bash(self):
        self.strength -= 1
        if self.strength <= 0:
            self.open()


class Fuel(Entity):
    class_char = "*"
    class_color = libtcod.amber

    def __init__(self, x, y, fov_map, con, game):
        Entity.__init__(self, x, y, self.class_char, self.class_color, False, Light(0, fov_map, con, game), Noise(x, y, 0, con, None), fov_map, con, game)
        self.amount = libtcod.random_get_int(0, 10, 30)

    def collect(self):
        self.x = None
        self.y = None
        return self.amount


class Stairs(Entity):
    class_char = "s"
    class_color = libtcod.light_green

    def __init__(self, x, y, fov_map, con, game):
        Entity.__init__(self, x, y, self.class_char, self.class_color, False,
                        Light(0, fov_map, con, game), Noise(x, y, 0, con, game), fov_map, con, game)
        self.game = game

    def descend(self):
        self.game.descend_floor()


class Closet(Entity):
    class_char = "c"
    class_color = libtcod.azure
    BASE_STRENGTH = 5

    def __init__(self, x, y, fov_map, con, game):
        Entity.__init__(self, x, y, self.class_char, libtcod.azure, True,
                        Light(0, fov_map, con, game), Noise(x, y, 0, con, game), fov_map, con, game)
        self.strength = self.BASE_STRENGTH
        self.is_destroyed = False
        self.destroyed_color = libtcod.darker_azure
        self.hiding_color = libtcod.light_azure

    def enter(self):
        self.color = self.hiding_color

    def exit(self):
        self.color = self.class_color

    def grab(self, x, y):
        self.x += self.x - x
        self.y += self.y - y

    def draw(self, fov_map, top_left, bottom_right, tiles):
        if libtcod.map_is_in_fov(fov_map, self.x, self.y) and tiles[self.x][self.y].brightness > 0:
            screen_x, screen_y = self.screen_xy(self, top_left, bottom_right, self.x, self.y)
            if self.is_destroyed:
                libtcod.console_set_default_foreground(self.con, self.destroyed_color)
            else:
                libtcod.console_set_default_foreground(self.con, self.color)
            libtcod.console_put_char(self.con, screen_x, screen_y, self.char, libtcod.BKGND_NONE)

    def bash(self):
        self.strength -= 1
        if self.strength <= 0:
            self.destroy()

    def destroy(self):
        self.exit()
        self.blocks_movement = False
        self.color = self.destroyed_color


class Torch(Entity):
    class_char = 't'
    lit_color = libtcod.orange
    unlit_color = libtcod.dark_orange

    def __init__(self, x, y, is_lit, fov_map, con, game):
        if is_lit:
            Entity.__init__(self, x, y, self.class_char, self.lit_color, False,
                            Light(libtcod.random_get_int(0, 2, 4), fov_map, con, game), Noise(x, y, 0, con, game), fov_map, con, None)
        else:
            Entity.__init__(self, x, y, self.class_char, self.unlit_color, False,
                            Light(libtcod.random_get_int(0, 2, 4), fov_map, con, game), Noise(x, y, 0, con, game), fov_map, con, None)
        self.is_lit = is_lit

    def toggle_lit(self, is_lit=None):
        if is_lit is None:
            self.is_lit = not self.is_lit
        else:
            self.is_lit = is_lit
        if self.is_lit:
            self.light.brightness = 5
        else:
            self.light.brightness = 0