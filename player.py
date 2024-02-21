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
import shapely

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
        self.hitbox = None  # contains the hitbox shapely object, used to calculate collision
        self.computer_player = computer_player
        self.left_player = left_player
        # keep player Client object with all information about user to display
        if client:
            self.client = client
        else:
            self.client = Client()
            if name:
                self.client.name = name
        self.x = None
        self.y = None
        self.player_size = None  # height and weight of square around player sprite

    def set_dead_texture(self):
        self.sprite.texture = self.__texture_left_dead if self.left_player else self.__texture_right_dead

    def set_alive_texture(self):
        self.sprite.texture = self.__texture_left if self.left_player else self.__texture_right

    def create_sprite(self, view):
        """this method must be called after creation of the game to create the sprite and hitbox,
        because their coordinates depends on game parameters.

        Does not check for collision with obstacles, so must be called before obstacle creation"""

        game = view.game
        self.player_size = self.__standard_height * game.game_field_ratio

        while True:
            # generating position and sprite
            self.x = random.uniform(self.player_size, game.x_edge - self.player_size)
            self.y = random.uniform(-game.y_edge + self.player_size, game.y_edge - self.player_size)
            if self.left_player:  # if player is from the left teem, just shifting him to the left side
                self.x -= game.x_edge

            self.sprite = arcade.Sprite(self.__texture_left if self.left_player else self.__texture_right,
                                        center_x=self.x * view.px_per_unit + view.graph_x_center,
                                        center_y=self.y * view.px_per_unit + view.graph_y_center,
                                        scale=self.player_size * view.px_per_unit / self.__texture_left.height)
            if (not game.players_sprites_list) or \
                    (not arcade.check_for_collision_with_list(self.sprite, game.players_sprites_list)):
                break  # repeat until sprite isn't overlapping any other sprite

        game.players_sprites_list.append(self.sprite)

        # creating hitbox
        self.hitbox = shapely.Point(self.x, self.y).buffer(self.player_size / 2 * 0.9)  # circular polygon

        # adding nick text object only once here
        self.nick = arcade.Text(self.client.name, start_x=self.sprite.center_x, start_y=self.sprite.bottom,
                                anchor_y='top', anchor_x='center', font_size=int(14 * view.window.scale),
                                color=arcade.color.WHITE)
