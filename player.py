"""
Copyright© 2024 Artur Pozniak <noi.kucia@gmail.com> or <noiszewczyk@gmail.com>.
All rights reserved.
This program is released under license GPL-3.0-or-later

This file is part of MathGraph.
MathGraph is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

MathGraph is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with MathGraph.
If not, see <https://www.gnu.org/licenses/>.
"""

import os
import random
import sys

import arcade

from client import Client

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)


class Player:
    __texture_left, __texture_right = arcade.load_texture_pair('textures/player_sprite.png')
    __texture_left_dead, __texture_right_dead = arcade.load_texture_pair('textures/player_sprite_dead.png')
    __standard_height = 1.5  # height of the player sprite in axes units for default map size (16 y)

    def __init__(self, computer_player: bool = True, client: Client = None, left_player=True, name: str = None):
        self.sprite = None
        self.nick = None
        self.alive = True
        self.computer_player = computer_player
        self.left_player = left_player
        # keep player Client object with all information about user to display
        if client:
            self.client = client
        else:
            self.client = Client()
            if name:
                self.client.name = name
        # graphic coordinates of player
        self.x = None
        self.y = None
        self.spawn_hitbox_size = None  # height and weight of square around player sprite which must be free

    def set_dead_texture(self):
        self.sprite.texture = self.__texture_left_dead if self.left_player else self.__texture_right_dead

    def set_alive_texture(self):
        self.sprite.texture = self.__texture_left if self.left_player else self.__texture_right

    def create_sprite(self, window):
        """this method must be called after creation of the game to create the sprite,
        bc it's coordinates depends on game parameters"""

        game = window.lobby.game
        GRAPH_TOP_EDGE = window.GRAPH_TOP_EDGE
        GRAPH_BOTTOM_EDGE = window.GRAPH_BOTTOM_EDGE
        GRAPH_LEFT_EDGE = int(
            window.SCREEN_WIDTH - (GRAPH_TOP_EDGE - GRAPH_BOTTOM_EDGE) * game.proportion_x2y) // 2
        GRAPH_RIGHT_EDGE = window.SCREEN_WIDTH - GRAPH_LEFT_EDGE
        self.spawn_hitbox_size = self.__standard_height * (game.y_edge / 16)
        pixels_per_unit = (GRAPH_RIGHT_EDGE - GRAPH_LEFT_EDGE) / (2 * game.x_edge)
        player_size_px = self.spawn_hitbox_size * pixels_per_unit

        while True:
            # choosing random x in the right part of the game field so that the sprite will not intersect borders
            rand_x = random.randint(
                int(window.SCREEN_X_CENTER + player_size_px / 2 * window.scale),
                int(GRAPH_RIGHT_EDGE - player_size_px / 2 * window.scale))
            if self.left_player:  # if player is from the left teem, just subtracting half of the game field width
                rand_x -= window.SCREEN_X_CENTER-GRAPH_LEFT_EDGE

            rand_y = random.randint(int(GRAPH_BOTTOM_EDGE + 15 * window.scale + player_size_px / 2),
                                    int(GRAPH_TOP_EDGE - 15 * window.scale - player_size_px / 2))

            sprite_scale = player_size_px / self.__texture_left.height
            self.sprite = arcade.Sprite(self.__texture_left if self.left_player else self.__texture_right,
                                        center_x=rand_x, center_y=rand_y, scale=sprite_scale)
            if (not window.lobby.game.players_sprites_list) or \
                    (not arcade.check_for_collision_with_list(self.sprite, window.lobby.game.players_sprites_list)):
                break  # repeat until sprite isn't overlapping any other sprite
        self.x = (self.sprite.center_x - window.SCREEN_X_CENTER) * window.lobby.game.x_edge * 2 / (
                GRAPH_RIGHT_EDGE - GRAPH_LEFT_EDGE)
        self.y = (self.sprite.center_y - (GRAPH_TOP_EDGE + GRAPH_BOTTOM_EDGE) / 2) * window.lobby.game.y_edge * 2 / (
                GRAPH_TOP_EDGE - GRAPH_BOTTOM_EDGE)

        window.lobby.game.players_sprites_list.append(self.sprite)
        window.lobby.game.players_sprites_list.initialize()  # to avoid lags during first drawing

        # adding nick text object only once here
        self.nick = arcade.Text(self.client.name, start_x=self.sprite.center_x,
                                start_y=self.sprite.bottom, anchor_y='top', anchor_x='center',
                                font_size=int(14 * window.scale), color=arcade.color.WHITE)
