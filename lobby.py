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

from player import Player
from arcade import View, Window, gui, load_texture
from game import Game, GameView
from UIFixedElements import *

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)


class Lobby:

    def __init__(self, player: Player = None, multiplayer=False):
        self.team1 = []
        self.team2 = []
        self.multiplayer = multiplayer
        if player:
            self.team1.append(player)
        self.game = None
        self.chat = None
        self.friendly_fire: bool = True
        self.auxiliary_marks: bool = True
        self.marks_frequency: int = 5
        self.max_time_s: int = 90
        self.obstacle_frequency: int = 20
        self.game_field_width: float = Game._proportion_x2y_max
        self.y_axis_limit: int = 16
        self.x_axis_limit: int = int(self.y_axis_limit * self.game_field_width)


class LobbyView(View):

    def __init__(self, window: Window):
        super().__init__(window)
        self.window = window
        self.lobby = window.lobby
        self.manager = gui.UIManager()
        self.manager.enable()
        self.temp_buttons_manager = gui.UIManager()
        self.objects_to_draw = []
        window.lobby.game: Game = None
        self.add_ui()

        self.background = load_texture('textures/Lobby_BG_4k.jpg')

        self.clients_sprites = []  # To keep avatar sprites
        self.client_names = []  # Keeps arcade.Text objects with names of clients

        self.clients_sprites_refresh()

    def on_show_view(self):
        self.manager.enable()
        self.temp_buttons_manager.enable()  # for little close buttons, which can appear and disappear

    def on_hide_view(self):
        self.manager.disable()
        self.temp_buttons_manager.disable()  # for little close buttons, which can appear and disappear

    def add_ui(self):
        bottom_button_scale = 0.75

        play_button_texture = load_texture('textures/LobbyPlayButton.png')
        play_button_texture_hovered = load_texture('textures/LobbyPlayButton_hovered.png')
        play_button = FixedUITextureButton(texture=play_button_texture,
                                           width=int(
                                               bottom_button_scale * self.window.scale * play_button_texture.width),
                                           height=int(
                                               bottom_button_scale * self.window.scale * play_button_texture.height),
                                           texture_hovered=
                                           play_button_texture_hovered)
        play_button.on_click = self.start_solo_game

        exit_button_texture = load_texture('textures/LobbyExitButton.png')
        exit_button_texture_hovered = load_texture('textures/LobbyExitButton_hovered.png')
        exit_button = FixedUITextureButton(texture=exit_button_texture,
                                           width=int(
                                               bottom_button_scale * self.window.scale * exit_button_texture.width),
                                           height=int(
                                               bottom_button_scale * self.window.scale * exit_button_texture.height),
                                           texture_hovered=
                                           exit_button_texture_hovered)
        exit_button.on_click = self.exit_lobby

        add_bot_button_texture = load_texture('textures/LobbyAddBotButton.png')
        add_bot_button_texture_hovered = load_texture('textures/LobbyAddBotButton_hovered.png')
        add_bot_button = FixedUITextureButton(texture=add_bot_button_texture,
                                              texture_hovered=add_bot_button_texture_hovered,
                                              width=int(
                                                  bottom_button_scale * self.window.scale * add_bot_button_texture.width),
                                              height=int(
                                                  bottom_button_scale * self.window.scale * add_bot_button_texture.height))
        add_bot_button.on_click = self.bot_add

        right_v_box = gui.UIBoxLayout(vertical=False, children=[add_bot_button, play_button, exit_button],
                                      space_between=int(75 * self.window.scale))

        right_anchor = gui.UIAnchorLayout()
        right_anchor.add(right_v_box, anchor_x='right', anchor_y='bottom', align_x=int(-315 * self.window.scale),
                         align_y=10)

        self.manager.add(right_anchor)
        self.settings_ui_add()

        # calculating coordinates for players_draw func
        self.team1_position = (int(475 * self.window.scale), int(110 * self.window.scale))
        self.team2_position = (int(1445 * self.window.scale), int(110 * self.window.scale))

        # teams labels preparing
        teams_label_font_size = int(36 * self.window.scale)
        self.objects_to_draw.append(arcade.Text('Team 1', self.team1_position[0], self.team1_position[1],
                                                color=arcade.color.WHITE,
                                                font_size=teams_label_font_size, bold=True, anchor_y='bottom',
                                                anchor_x='center'))
        self.objects_to_draw.append(arcade.Text('Team 2', self.team2_position[0], self.team2_position[1],
                                                color=arcade.color.WHITE,
                                                font_size=teams_label_font_size, bold=True, anchor_y='bottom',
                                                anchor_x='center'))

    def settings_ui_add(self):
        lobby = self.window.lobby

        setting_box_scale = 0.25 * self.window.scale
        setting_box_texture = load_texture('textures/LobbySettingsBox.png')
        setting_box_height = setting_box_texture.height * setting_box_scale
        setting_box_width = setting_box_texture.width * setting_box_scale
        self.settings_box = arcade.Sprite(setting_box_texture, setting_box_scale,
                                          int(self.window.width - setting_box_width / 2),
                                          int(self.window.height - setting_box_height / 2))

        checkbox_empty_texture = load_texture('textures/CheckBoxBlue_empty.png')
        checkbox_pressed_texture = load_texture('textures/CheckBoxBlue_pressed.png')
        checkbox_scale = 0.25 * self.window.scale
        checkbox_color = (128, 245, 255)
        checkbox_font = 'Arial'
        checkbox_font_size = int(22 * self.window.scale)
        checkbox_vertical_offset = int(22 * self.window.scale)

        slider_width = int(330 * self.window.scale)
        slider_height = int(30 * self.window.scale)

        ui_anchor = gui.UIAnchorLayout()

        # auxiliary marks toggle
        self.objects_to_draw.append(
            arcade.Text(text='Marks on axes', font_size=checkbox_font_size, font_name=checkbox_font,
                        color=checkbox_color, anchor_y='center', anchor_x='left',
                        start_x=self.window.width + 5 - int(setting_box_width - 50 * self.window.scale
                                                            - checkbox_empty_texture.width * checkbox_scale),
                        start_y=int(self.window.height - (0.25 * setting_box_height)
                                    - checkbox_empty_texture.height * checkbox_scale / 2)
                        )
        )

        self.is_axes_marked_box = FixedUITextureToggle(width=int(checkbox_empty_texture.width * checkbox_scale),
                                                       height=int(checkbox_empty_texture.height * checkbox_scale),
                                                       on_texture=checkbox_pressed_texture,
                                                       off_texture=checkbox_empty_texture)
        self.is_axes_marked_box.value = lobby.auxiliary_marks

        @self.is_axes_marked_box.event('on_change')
        def change(event):
            lobby.auxiliary_marks = not lobby.auxiliary_marks

        ui_anchor.add(self.is_axes_marked_box, anchor_x='right', anchor_y='top',
                      align_y=-int(0.25 * setting_box_height),
                      align_x=-int(setting_box_width - 50 * self.window.scale
                                   - checkbox_empty_texture.width * checkbox_scale)
                      )

        # friendly fire toggle
        self.objects_to_draw.append(
            arcade.Text(text='Friendly fire allow', font_size=checkbox_font_size, font_name=checkbox_font,
                        color=checkbox_color,
                        anchor_y='center', anchor_x='left',
                        start_x=self.window.width - int(setting_box_width - 55 * self.window.scale
                                                        - checkbox_empty_texture.width * checkbox_scale),
                        start_y=int(self.window.height - 0.25 * setting_box_height - 1.5 * checkbox_empty_texture.height
                                    * checkbox_scale - 1 * checkbox_vertical_offset)
                        )
        )
        self.is_friendly_fire_box = FixedUITextureToggle(width=int(checkbox_empty_texture.width * checkbox_scale),
                                                         height=int(checkbox_empty_texture.height * checkbox_scale),
                                                         on_texture=checkbox_pressed_texture,
                                                         off_texture=checkbox_empty_texture)
        self.is_friendly_fire_box.value = lobby.friendly_fire

        @self.is_friendly_fire_box.event('on_change')
        def change(event):
            lobby.friendly_fire = not lobby.friendly_fire

        ui_anchor.add(self.is_friendly_fire_box, anchor_x='right', anchor_y='top',
                      align_x=-int(setting_box_width - 50 * self.window.scale
                                   - checkbox_empty_texture.width * checkbox_scale),
                      align_y=-int(0.25 * setting_box_height)
                              - 1 * int(checkbox_empty_texture.height * checkbox_scale) - 1 * checkbox_vertical_offset)

        slider_style = {  # style for sliders in setting box
            "normal": gui.UISliderStyle(
                bg=(128, 245, 255, 255),
                border=(50, 50, 50, 255),
                filled_bar=(101, 225, 236, 255),
                unfilled_bar=(50, 50, 50, 255)
            ),
            "hover": gui.UISliderStyle(
                bg=(255, 255, 255, 255),
                border=(50, 50, 50, 255),
                filled_bar=(101, 225, 236, 255),
                unfilled_bar=(50, 50, 50, 255),
                border_width=0
            ),
            "press": gui.UISliderStyle(
                bg=(255, 255, 255, 255),
                border=(50, 50, 50, 255),
                filled_bar=(101, 225, 236, 255),
                unfilled_bar=(50, 50, 50, 255),

            ),
            "disabled": gui.UISliderStyle()
        }

        # Y axis limit
        self.objects_to_draw.append(
            arcade.Text(text='Y axis limit:', font_size=checkbox_font_size, font_name=checkbox_font,
                        color=checkbox_color,
                        anchor_y='top', anchor_x='left',
                        start_x=self.window.width + 5 - int(setting_box_width
                                                            - 50 * self.window.scale),
                        start_y=int(self.window.height - (0.25 * setting_box_height)
                                    - checkbox_empty_texture.height * checkbox_scale / 2 -
                                    1.5 * int(
                            checkbox_empty_texture.height * checkbox_scale) - 1.8 * checkbox_vertical_offset)))

        self.y_limit_slider = gui.UISlider(value=int((lobby.y_axis_limit - 10) / 0.9), min_value=0,
                                           max_value=100, width=slider_width,
                                           height=slider_height, style=slider_style)
        ui_anchor.add(self.y_limit_slider, anchor_y='top', anchor_x='left',
                      align_x=self.window.width - int(setting_box_width
                                                      - 50 * self.window.scale),
                      align_y=- (0.25 * setting_box_height)
                              - checkbox_empty_texture.height * checkbox_scale / 2 -
                              1.5 * int(checkbox_empty_texture.height * checkbox_scale)
                              - 2.3 * checkbox_vertical_offset - int(checkbox_font_size))
        self.y_limit_value_text = arcade.Text(
            anchor_y='top', anchor_x='left',
            start_x=int(self.window.width - setting_box_width + 225 * self.window.scale),
            start_y=int(self.window.height - 0.25 * setting_box_height
                        - 2 * int(checkbox_empty_texture.height * checkbox_scale) - 1.8 * checkbox_vertical_offset),
            text=str(lobby.y_axis_limit), font_name=checkbox_font, font_size=checkbox_font_size
        )
        self.objects_to_draw.append(self.y_limit_value_text)

        @self.y_limit_slider.event("on_change")
        def change(event):
            lobby.y_axis_limit = int(10 + self.y_limit_slider.value * 90 / 100)
            lobby.x_axis_limit = int(lobby.game_field_width * lobby.y_axis_limit)
            self.y_limit_value_text.text = str(lobby.y_axis_limit)
            self.x_edge_value_text.text = str(lobby.x_axis_limit)

        # game field width ( x2y proportion )
        self.objects_to_draw.append(
            arcade.Text(text='game field width:', font_size=checkbox_font_size, font_name=checkbox_font,
                        color=checkbox_color,
                        anchor_y='top', anchor_x='left',
                        start_x=self.window.width - int(setting_box_width - 55 * self.window.scale),
                        start_y=int(self.window.height - (0.25 * setting_box_height)
                                    - 3 * int(checkbox_empty_texture.height * checkbox_scale)
                                    - 2 * checkbox_vertical_offset)
                        )
        )

        self.width_slider = gui.UISlider(value=int((lobby.game_field_width-1)*100/(Game._proportion_x2y_max - 1)),
                                         min_value=0, max_value=100,  width=slider_width,
                                         height=slider_height, style=slider_style)

        @self.width_slider.event("on_change")
        def change(event):
            lobby.game_field_width = self.width_slider.value * (Game._proportion_x2y_max - 1) / 100 + 1
            lobby.x_axis_limit = int(lobby.game_field_width * lobby.y_axis_limit)
            self.x_edge_value_text.text = str(lobby.x_axis_limit)

        ui_anchor.add(self.width_slider, anchor_y='top', anchor_x='left',
                      align_x=self.window.width - int(setting_box_width
                                                      - 50 * self.window.scale),
                      align_y=- (0.25 * setting_box_height)
                              - 3 * int(checkbox_empty_texture.height * checkbox_scale)
                              - 2 * checkbox_vertical_offset - int(checkbox_font_size * 1.5)
                      )

        # x axis limit text
        self.objects_to_draw.append(
            arcade.Text(text='X axis limit:', font_size=checkbox_font_size, font_name=checkbox_font,
                        anchor_y='top', anchor_x='left', color=checkbox_color,
                        start_x=self.window.width + 5 - int(setting_box_width
                                                            - 50 * self.window.scale),
                        start_y=int(self.window.height - (0.25 * setting_box_height)
                                    - checkbox_empty_texture.height * checkbox_scale / 2 -
                                    2 * int(checkbox_empty_texture.height * checkbox_scale)
                                    - 2.5 * checkbox_vertical_offset - int(checkbox_font_size * 2.5) - int(
                            30 * self.window.scale))
                        )
        )
        self.x_edge_value_text = arcade.Text(
            text=str(lobby.x_axis_limit), font_size=checkbox_font_size, font_name=checkbox_font, anchor_y='top',
            anchor_x='left',
            start_x=self.window.width - int(setting_box_width - 225 * self.window.scale),
            start_y=int(self.window.height - 0.25 * setting_box_height
                        - 2.5 * int(checkbox_empty_texture.height * checkbox_scale) - 2.5 * checkbox_vertical_offset
                        - 2.5 * checkbox_font_size - 30 * self.window.scale)
        )
        self.objects_to_draw.append(self.x_edge_value_text)

        # marks frequency
        self.objects_to_draw.append(
            arcade.Text(text='Marks frequency:', font_size=checkbox_font_size, font_name=checkbox_font,
                        color=checkbox_color, anchor_y='center', anchor_x='left',
                        start_x=self.window.width - int(setting_box_width - 425 * self.window.scale
                                                        - checkbox_empty_texture.width * checkbox_scale),
                        start_y=int(self.window.height - 0.25 * setting_box_height
                                    - checkbox_empty_texture.height * checkbox_scale / 2)
                        )
        )

        self.marks_frequency_slider = gui.UISlider(value=(lobby.marks_frequency - 1) / 49 * 100, min_value=0,
                                                   max_value=100, width=slider_width,
                                                   height=slider_height, style=slider_style)

        @self.marks_frequency_slider.event("on_change")
        def change(event):
            lobby.marks_frequency = int(self.marks_frequency_slider.value * 49 / 100) + 1
            self.marks_frequency_value_text.text = str(lobby.marks_frequency)

        ui_anchor.add(self.marks_frequency_slider, anchor_y='top', anchor_x='left',
                      align_x=self.window.width - int(setting_box_width - 420 * self.window.scale
                                                      - checkbox_empty_texture.width * checkbox_scale),
                      align_y=- 0.25 * setting_box_height
                              - checkbox_empty_texture.height * checkbox_scale / 2 - checkbox_vertical_offset)

        self.marks_frequency_value_text = arcade.Text(
            str(lobby.marks_frequency), anchor_x='left', anchor_y='center',
            start_x=self.window.width - int(setting_box_width - 665 * self.window.scale 
                                            - checkbox_empty_texture.width * checkbox_scale),
            start_y=int(self.window.height - 0.25 * setting_box_height
                        - checkbox_empty_texture.height * checkbox_scale / 2),
            font_size=checkbox_font_size, font_name=checkbox_font)
        self.objects_to_draw.append(self.marks_frequency_value_text)

        # time limit setting
        self.objects_to_draw.append(
            arcade.Text(
                'Time limit (s) :', anchor_x='left', anchor_y='top',
                start_x=self.window.width - int(setting_box_width - 425 * self.window.scale
                                                - checkbox_empty_texture.width * checkbox_scale),
                start_y=int(self.window.height - 0.25 * setting_box_height
                            - 3 * checkbox_empty_texture.height * checkbox_scale / 2),
                font_size=checkbox_font_size, font_name=checkbox_font, color=checkbox_color)
        )

        self.time_limit_text = arcade.Text(
            str(lobby.max_time_s), anchor_x='left', anchor_y='top',
            start_x=self.window.width - int(setting_box_width - 665 * self.window.scale - checkbox_empty_texture.width
                                            * checkbox_scale),
            start_y=int(self.window.height - 0.25 * setting_box_height
                        - 3 * checkbox_empty_texture.height * checkbox_scale / 2),
            font_size=checkbox_font_size, font_name=checkbox_font
        )
        self.objects_to_draw.append(self.time_limit_text)

        self.time_limit_slider = gui.UISlider(value=int((lobby.max_time_s - 30) / 120 * 100), min_value=0,
                                              max_value=100, width=slider_width,
                                              height=slider_height, style=slider_style)
        @self.time_limit_slider.event("on_change")
        def change(event):
            lobby.max_time_s = int(self.time_limit_slider.value * 120 / 100) + 30
            self.time_limit_text.text = str(lobby.max_time_s)

        ui_anchor.add(self.time_limit_slider, anchor_y='top', anchor_x='left',
                      align_x=self.window.width - int(setting_box_width - 420 * self.window.scale
                                                      - checkbox_empty_texture.width * checkbox_scale),
                      align_y=int(- 0.25 * setting_box_height
                                  - 1.5 * checkbox_empty_texture.height * checkbox_scale
                                  - checkbox_font_size - 0.5 * checkbox_vertical_offset)
                      )

        # obstacle frequency
        self.objects_to_draw.append(
            arcade.Text('obstacle frequency:', anchor_x='left', anchor_y='top',
                        start_x=self.window.width + 5 - int(setting_box_width - 420 * self.window.scale
                                                            - checkbox_empty_texture.width * checkbox_scale),
                        start_y=int(self.window.height - 0.25 * setting_box_height
                                    - 1.5 * checkbox_empty_texture.height * checkbox_scale
                                    - checkbox_font_size - 0.5 * checkbox_vertical_offset - 30 * self.window.scale),
                        font_size=checkbox_font_size, font_name=checkbox_font, color=checkbox_color
                        )
        )

        self.obstacle_frequency_value_text = arcade.Text(
            str(lobby.obstacle_frequency), anchor_x='left', anchor_y='top',
            start_x=self.window.width - int(setting_box_width - 680 * self.window.scale
                                            - checkbox_empty_texture.width * checkbox_scale),
            start_y=int(self.window.height - 0.25 * setting_box_height
                        - 1.5 * checkbox_empty_texture.height * checkbox_scale
                        - checkbox_font_size - 0.5 * checkbox_vertical_offset - slider_height),
            font_size=checkbox_font_size, font_name=checkbox_font, color=(255, 255, 255)
        )
        self.objects_to_draw.append(self.obstacle_frequency_value_text)

        self.obstacle_frequency_slider = gui.UISlider(
            value=lobby.obstacle_frequency, min_value=0, max_value=100, width=slider_width,
            height=slider_height, style=slider_style
        )

        @self.obstacle_frequency_slider.event("on_change")
        def change(event):
            lobby.obstacle_frequency = int(self.obstacle_frequency_slider.value)
            self.obstacle_frequency_value_text.text = str(lobby.obstacle_frequency)

        ui_anchor.add(self.obstacle_frequency_slider, anchor_y='top', anchor_x='left',
                      align_x=self.window.width - int(setting_box_width - 420 * self.window.scale
                                                      - checkbox_empty_texture.width * checkbox_scale),
                      align_y=int(- 0.25 * setting_box_height
                                  - 1.5 * checkbox_empty_texture.height * checkbox_scale
                                  - checkbox_font_size - 0.75 * checkbox_vertical_offset - 2 * slider_height)
                      )

        self.manager.add(ui_anchor)

    def on_draw(self):
        self.clear()
        arcade.start_render()
        arcade.draw_lrwh_rectangle_textured(0, 0, self.window.SCREEN_WIDTH, self.window.SCREEN_HEIGHT,
                                            self.background)  # drawing background image
        self.players_draw()
        self.settings_box.draw()
        self.manager.draw()
        for object in self.objects_to_draw:
            object.draw()
        arcade.finish_render()

    def on_update(self, delta_time: float):
        if not self.lobby.multiplayer:
            return

    def bot_add(self, event):
        max_players_team = 4
        lobby = self.window.lobby
        with open('resources/bot_names.txt', 'r') as file:
            names = file.readlines()
        player = Player(name=random.choice(names))
        if len(lobby.team1) > max_players_team:
            if len(lobby.team2) > max_players_team: return  # all teams are full
            lobby.team2.append(player)
        else:
            lobby.team1.append(player)

        self.clients_sprites_refresh()

    def exit_lobby(self, event):
        from menu import MenuView
        view = MenuView(self.window)
        self.window.show_view(view)

    def start_solo_game(self, event):

        # preparing new game
        game = self.lobby.game = Game(multiplayer=False)
        game.axes_marked = self.lobby.auxiliary_marks
        game.marks_frequency = self.lobby.marks_frequency
        game.friendly_fire = self.lobby.friendly_fire
        game.y_edge = self.lobby.y_axis_limit
        game.x_edge = self.lobby.x_axis_limit
        game.proportion_x2y = self.lobby.game_field_width
        game.max_time_s = self.lobby.max_time_s
        game.obstacle_frequency = self.lobby.obstacle_frequency

        # adding players from lobby
        for player in self.window.lobby.team1:
            if player.client == self.window.client:
                self.lobby.game.left_team = self.lobby.team1
                self.window.lobby.game.right_team = self.lobby.team2
                break
        else:
            for player in self.window.lobby.team2:
                if player.client == self.window.client:
                    self.lobby.game.left_team = self.window.lobby.team2
                    self.lobby.game.right_team = self.lobby.team1
                    break
            else:
                raise Exception('You are not a member of any team!')

        game.prepare()
        view = GameView(self.window)
        self.window.show_view(view)

    def clients_sprites_refresh(self):
        """ creating sprites of avatar, border,
        name label of all clients in players list"""

        avatar_width = int(160 * self.window.scale)
        space_between_avatars = int(25 * self.window.scale)
        avatar_y_offset = int(97 * self.window.scale + avatar_width / 2)
        nick_font = 'Raleway'

        # deleting old objects
        self.clients_sprites.clear()
        self.temp_buttons_manager.clear()
        self.client_names.clear()

        # creating new objects
        for player in self.lobby.team1 + self.lobby.team2:
            team, team_position = (self.lobby.team1, self.team1_position) if player in self.lobby.team1 else \
                (self.lobby.team2, self.team2_position)

            # center x avatar coordinate
            x_pos = int(avatar_width * (len(team) - 1) / 2 + (
                    len(team) - 1) / 2 * space_between_avatars +
                        team_position[0] - team.index(player) * (avatar_width + space_between_avatars))

            # adding avatar sprite
            self.clients_sprites.append(arcade.Sprite(player.client.avatar,
                                                      scale=avatar_width / player.client.avatar.width,
                                                      center_x=x_pos, center_y=team_position[1] + avatar_y_offset))

            # adding name label
            is_user = player.client == self.window.client
            name = arcade.Text(player.client.name, x_pos,
                               int(team_position[1] + avatar_y_offset - avatar_width / 2),
                               color=(198, 0, 0) if is_user else arcade.color.WHITE,
                               font_size=int(17 * self.window.scale),
                               anchor_x='center', anchor_y='top', italic=False, bold=is_user,
                               width=avatar_width, multiline=True, font_name=nick_font)
            name._label.set_style("wrap", "char")  # setting wrapping to char method
            self.client_names.append(name)

            # adding close and swap buttons
            close_texture = load_texture('textures/avatar_close_32px.png')
            close_texture_hovered = load_texture('textures/avatar_close_32px_hovered.png')
            swap_button_texture = load_texture('textures/team_swap_32px.png')

            if not is_user:  # user cannot kick himself
                close_button = FixedUITextureButton(texture=close_texture,
                                                    x=int(x_pos + avatar_width / 2 - 32 * self.window.scale),
                                                    y=int(team_position[1] + avatar_y_offset - 32
                                                          * self.window.scale + avatar_width / 2),
                                                    width=int(32 * self.window.scale),
                                                    height=int(32 * self.window.scale),
                                                    texture_hovered=close_texture_hovered)
                quit_func = QuitFunction(player, self)
                close_button.on_click = quit_func.kick
                self.temp_buttons_manager.add(close_button)
            swap_button = FixedUITextureButton(texture=swap_button_texture,
                                               x=int(x_pos + avatar_width / 2 - 66 * self.window.scale
                                                     + (36 if self.window.client == player.client else 0)),
                                               y=int(team_position[1] + avatar_y_offset - 32
                                                     * self.window.scale + avatar_width / 2),
                                               width=int(32 * self.window.scale),
                                               height=int(32 * self.window.scale))
            swap_func = SwapFunction(player, self)
            swap_button.on_click = swap_func.swap
            self.temp_buttons_manager.add(swap_button)

    def players_draw(self):
        for client in self.clients_sprites:
            client.draw()
            client.draw_hit_box(color=(255, 255, 255))
        for name in self.client_names: name.draw()
        self.temp_buttons_manager.draw()


class QuitFunction:

    def __init__(self, player: Player, view):
        self.player = player
        self.view = view
        self.lobby = view.window.lobby

    def kick(self, event):
        if self.player in self.lobby.team1:
            self.lobby.team1.remove(self.player)
        else:
            self.lobby.team2.remove(self.player)
        self.view.clients_sprites_refresh()  # creating new sprites with new buttons


class SwapFunction:

    def __init__(self, player: Player, view):
        self.player = player
        self.view = view
        self.lobby = view.window.lobby

    def swap(self, event):
        if self.player in self.lobby.team1:
            if len(self.lobby.team2) > 4:
                return  # team 2 is full
            self.lobby.team1.remove(self.player)
            self.lobby.team2.append(self.player)
        else:
            if len(self.lobby.team1) > 4:
                return  # team 1 is full
            self.lobby.team2.remove(self.player)
            self.lobby.team1.append(self.player)
        self.view.clients_sprites_refresh()  # creating new sprites with new buttons
