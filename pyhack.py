#!usr/bin/python

import libtcodpy as libtcod
import entity
from level import Level

# constants
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
MAP_WIDTH = 80
MAP_HEIGHT = 40
LIMIT_FPS = 25

# libtcod specific settings
libtcod.console_set_custom_font(b'terminal12x12_gs_ro.png',
                                libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_ASCII_INROW)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, b'pyhack', False)
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
libtcod.sys_set_fps(LIMIT_FPS)
libtcod.console_disable_keyboard_repeat()


class Pyhack:
    def __init__(self):
        self.level = Level(MAP_WIDTH, MAP_HEIGHT, con)
        self.player = entity.Player(25, 23, '@', libtcod.white, con, self)
        self.monster = entity.Monster(25, 24, '&', libtcod.red, con, self, self.level, self.player)
        self.entities = [self.player, self.monster]
        self.turn_based = True
        self.level.create_map(self.player, self)
        self.floor = 0

    def handle_keys(self):
        # handles user input

        if self.turn_based:
            # causes the game to pause to wait for user input
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
            self.level.draw(self.player)

            for entity in reversed(self.entities):
                entity.draw(self.level.fov_map)

            libtcod.console_set_color_control(con, libtcod.white, libtcod.black)
            libtcod.console_print(con, 5, 45, "Lantern fuel: " + str(int(self.player.fuel)) + "  ")
            libtcod.console_print(con, 5, 46, "Sanity: " + str(int(self.player.sanity)) + "  ")
            libtcod.console_print(con, 5, 47, "Health: " + str(int(self.player.health)) + "  ")

            libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
            libtcod.console_flush()

            for entity in reversed(self.entities):
                entity.clear()

            self.handle_keys()
            self.player.update()

            # set the game to turn based if the monster is not spawned and real time if it is
            self.turn_based = not self.monster.update()

            return True
        else:
            self.game_over()
            return False

    def descend_floor(self):
        self.floor += 1
        self.level = Level(MAP_WIDTH, MAP_HEIGHT, con)
        self.monster = entity.Monster(25, 24, '&', libtcod.red, con, self, self.level, self.player)
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
            game_over_result = "You have gone stark raving mad, there is no hope of survival"

        libtcod.console_clear(con)

        libtcod.console_set_default_foreground(con, libtcod.red)
        libtcod.console_print(con, SCREEN_WIDTH / 2 - len(game_over_string) / 2, SCREEN_HEIGHT / 2 - 5,
                              game_over_string)
        libtcod.console_set_default_foreground(con, libtcod.white)
        libtcod.console_print(con, SCREEN_WIDTH / 2 - len(game_over_result) / 2, SCREEN_HEIGHT / 2 - 4,
                              game_over_result)
        libtcod.console_print(con, SCREEN_WIDTH / 2 - len(game_over_score) / 2, SCREEN_HEIGHT / 2 - 2,
                              game_over_score)
        libtcod.console_print(con, SCREEN_WIDTH / 2 - len(game_over_instructions) / 2, SCREEN_HEIGHT / 2 - 1,
                              game_over_instructions)
        libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
        libtcod.console_flush()

        libtcod.console_wait_for_keypress(True)


def main():
    # initializes the Pyhack object
    game = Pyhack()

    # constantly renders while the program window is still open
    while not libtcod.console_is_window_closed():
        libtcod.console_set_default_foreground(con, libtcod.white)
        if not game.render():
            return


if __name__ == "__main__":
    # program starting point
    # run the main method
    main()