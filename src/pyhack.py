# !usr/bin/python

from lib import libtcodpy as libtcod
from src import entity
from src.level import Level
from src.level import Tile
from src.pathing import Light

# constants
SCREEN_WIDTH = 59
SCREEN_HEIGHT = 25
INTERFACE_HEIGHT = 10
MAP_WIDTH = 80
MAP_HEIGHT = 60
LIMIT_FPS = 25

# libtcod specific settings
libtcod.console_set_custom_font(b'res/terminal12x12_gs_ro.png',
                                libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_ASCII_INROW)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT + INTERFACE_HEIGHT, b'pyhack', False)
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT + INTERFACE_HEIGHT)
libtcod.sys_set_fps(LIMIT_FPS)
libtcod.console_disable_keyboard_repeat()


class Pyhack:
    def __init__(self):
        self.level = Level(MAP_WIDTH, MAP_HEIGHT, con, self)
        self.player = entity.Player(0, 0, self.level.fov_map, con, self)
        self.monster = entity.Monster(0, 0, self.level, self.player, self.level.fov_map, con, self)
        self.entities = [self.player, self.monster]
        self.turn_based = True
        self.level.create_map(self.player, self)
        self.floor = 0

    def handle_keys(self):
        # handles user input

        if self.turn_based:
            # game will pause to wait for user input
            key = libtcod.console_wait_for_keypress(True)
        else:
            # game will continue without user input
            key = libtcod.console_check_for_keypress(libtcod.KEY_PRESSED)
        if not self.player.performing_action:

            if key.vk == libtcod.KEY_LEFT:
                self.player.move(-1, 0, self.level.tiles)

            elif key.vk == libtcod.KEY_RIGHT:
                self.player.move(1, 0, self.level.tiles)

            elif key.vk == libtcod.KEY_UP:
                self.player.move(0, -1, self.level.tiles)

            elif key.vk == libtcod.KEY_DOWN:
                self.player.move(0, 1, self.level.tiles)

            elif key.c == ord('l'):
                self.player.toggle_lamp()

            elif key.c == ord('o'):
                self.player.performing_action = True
                self.player.next_action = entity.NextAction.open

            elif key.c == ord('p'):
                self.player.performing_action = True
                self.player.next_action = entity.NextAction.close

            elif key.c == ord('c'):
                self.player.performing_action = True
                self.player.next_action = entity.NextAction.pick_up

            elif key.c == ord('d'):
                self.player.performing_action = True
                self.player.next_action = entity.NextAction.descend

            elif key.c == ord('i'):
                self.player.performing_action = True
                self.player.next_action = entity.NextAction.grab

            elif key.c == ord('u'):
                self.player.drop()
        else:
            if key.vk == libtcod.KEY_LEFT:
                self.player.perform_action(-1, 0)

            elif key.vk == libtcod.KEY_RIGHT:
                self.player.perform_action(1, 0)

            elif key.vk == libtcod.KEY_UP:
                self.player.perform_action(0, -1)

            elif key.vk == libtcod.KEY_DOWN:
                self.player.perform_action(0, 1)

    def render(self):
        if self.player.health > 0 and self.player.sanity > 0:
            # renders the game components
            libtcod.console_clear(con)

            Light.clear_brightness(self.level.tiles)

            for entity in reversed(self.entities):
                entity.light.calculate_tile_brightness(self.level.tiles, entity.x, entity.y, self.level.top_left, self.level.bottom_right, self.level.fov_map)

            self.level.draw(self.player, SCREEN_WIDTH, SCREEN_HEIGHT)

            for entity in reversed(self.entities):
                entity.draw(self.level.fov_map, self.level.top_left, self.level.bottom_right, self.level.tiles)

            libtcod.console_set_color_control(con, libtcod.white, libtcod.black)
            libtcod.console_print(con, 5, SCREEN_HEIGHT + 4, "Fue: " + str(int(self.player.fuel)))
            libtcod.console_print(con, 5, SCREEN_HEIGHT + 5, "San: " + str(int(self.player.sanity)))
            libtcod.console_print(con, 5, SCREEN_HEIGHT + 6, "Hea: " + str(int(self.player.health)))
            libtcod.console_print(con, 5, SCREEN_HEIGHT + 7, "Sta: " + str(int(self.player.stamina)))

            libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT + 10, 0, 0, 0)
            libtcod.console_flush()

            for entity in reversed(self.entities):
                entity.clear()

            self.player.update()
            self.monster.update(self.level.tiles)

            self.handle_keys()

            return True
        else:
            self.game_over()
            return False

    def descend_floor(self):
        self.floor += 1
        self.level = Level(MAP_WIDTH, MAP_HEIGHT, con, self)
        self.monster = entity.Monster(25, 24, self.level, self.player, self.level.fov_map, con, self)
        self.entities = [self.player, self.monster]
        self.level.create_map(self.player, self)

    def game_over(self):
        game_over_string = "GAME OVER"
        game_over_result = ""
        game_over_score = "You made it " + str(self.floor) + " floors"
        game_over_instructions = "Press any key to exit"
        if self.player.health <= 0:
            game_over_result = "You have died"
        elif self.player.sanity <= 0:
            game_over_result = "You have gone stark raving mad"

        libtcod.console_clear(con)

        libtcod.console_set_default_foreground(con, libtcod.red)
        libtcod.console_print(con, round(SCREEN_WIDTH / 2 - len(game_over_string) / 2), round(SCREEN_HEIGHT / 2 - 5),
                              game_over_string)
        libtcod.console_set_default_foreground(con, libtcod.white)
        libtcod.console_print(con, round(SCREEN_WIDTH / 2 - len(game_over_result) / 2), round(SCREEN_HEIGHT / 2 - 4),
                              game_over_result)
        libtcod.console_print(con, round(SCREEN_WIDTH / 2 - len(game_over_score) / 2), round(SCREEN_HEIGHT / 2 - 2),
                              game_over_score)
        libtcod.console_print(con, round(SCREEN_WIDTH / 2 - len(game_over_instructions) / 2),
                              round(SCREEN_HEIGHT / 2 - 1), game_over_instructions)
        libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT + INTERFACE_HEIGHT, 0, 0, 0)
        libtcod.console_flush()

        libtcod.console_wait_for_keypress(True)


def main():
    # initializes the Pyhack object
    game = Pyhack()
    game.level.draw(game.player, SCREEN_WIDTH, SCREEN_HEIGHT)

    # constantly renders while the program window is still open
    while not libtcod.console_is_window_closed():
        libtcod.console_set_default_foreground(con, libtcod.white)
        if not game.render():
            return


if __name__ == "__main__":
    # program starting point
    # run the main method
    main()