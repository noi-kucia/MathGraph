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
import time

from arcade import View, gui, load_texture
from UIFixedElements import *
from lobby import Lobby
from player import Player


def exit_game(event):
    arcade.exit()


class MenuView(View):

    def __init__(self, window):
        super().__init__(window)
        self.background = load_texture('textures/MainMenuBackgroundLogo.png')
        self.manager = gui.UIManager()  # for all gui elements
        self.manager.enable()
        self.add_ui()

    def on_show_view(self):
        self.manager.enable()

    def on_hide_view(self):
        self.manager.disable()

    def add_ui(self):
        settings_texture = load_texture('textures/Settings_button_2048.png')
        solo_game_texture = load_texture('textures/SoloGame_button_2048.png')
        multiplayer_texture = load_texture('textures/Multiplayer_button_2048.png')
        exit_texture = load_texture('textures/Exit_button_2048.png')

        settings_texture_hover = load_texture('textures/Settings_button_2048_hover.png')
        solo_game_texture_hover = load_texture('textures/SoloGame_button_2048_hover.png')
        multiplayer_texture_hover = load_texture('textures/Multiplayer_button_2048_hover.png')
        exit_texture_hover = load_texture('textures/Exit_button_2048_hover.png')

        self.solo_game_button = FixedUITextureButton(texture_hovered=solo_game_texture_hover,
                                                     texture=solo_game_texture, size_hint=(1, 0.32))

        self.solo_game_button.on_click = self.solo_game_button_pressed
        multiplayer_button = FixedUITextureButton(texture_hovered=multiplayer_texture_hover,
                                                  texture=multiplayer_texture,
                                                  size_hint=(1, 0.33))
        multiplayer_button.on_click = self.multiplayer_game_start
        quit_button = FixedUITextureButton(texture_hovered=exit_texture_hover,
                                           texture=exit_texture, size_hint=(1, 0.32))
        quit_button.on_click = exit_game
        self.settings_button = FixedUITextureButton(texture_hovered=settings_texture_hover,
                                                    texture=settings_texture, size_hint=(1, 0.32))
        self.settings_button.on_click = self.settings

        self.button_box = gui.widgets.layout.UIBoxLayout(space_between=0, size_hint=(0.3, 0.45))
        self.button_box.add(self.solo_game_button)
        self.button_box.add(multiplayer_button)
        self.button_box.add(self.settings_button)
        self.button_box.add(quit_button)

        ui_anchor_layout = gui.widgets.layout.UIAnchorLayout(size_hint=(1, 1))
        ui_anchor_layout.add(child=self.button_box, anchor_y='bottom',
                             align_y=int(180 * self.window.scale))

        self.manager.add(widget=ui_anchor_layout)

    def settings(self, event):
        from settings import SettingsView
        view = SettingsView(self.window)
        self.window.show_view(view)

    def solo_game_button_pressed(self, event):
        """creating new lobby and calling lobby view"""
        user = self.window.client
        user_player = Player(False, user)  # immediately creating user player
        self.window.lobby = Lobby(user_player)

        # showing lobby view
        from lobby import LobbyView
        view = LobbyView(self.window)
        self.window.show_view(view)

    def multiplayer_game_start(self, event):
        message_box = gui.UIMessageBox(
            width=300,
            height=200,
            message_text='Multiplayer is not available yet :<\nin progres..',
            buttons=["Ok"],
        )
        self.manager.add(message_box)

    def on_draw(self):
        game = self.window
        self.clear()
        arcade.start_render()
        arcade.draw_lrwh_rectangle_textured(0, 0, game.SCREEN_WIDTH, game.SCREEN_HEIGHT,
                                            self.background)  # drawing background image
        self.avatar_draw()
        self.manager.draw()
        arcade.finish_render()

    def avatar_draw(self):
        avatar_box_texture = load_texture('textures/AvatarBox_menu.png')
        avatar_box_scale = 0.22 * self.window.scale
        avatar_center_x = int(self.window.width - avatar_box_texture.width * avatar_box_scale) + int(
            avatar_box_texture.width * avatar_box_scale / 2)
        avatar_center_y = int(self.window.height - avatar_box_texture.height * avatar_box_scale) + int(
            avatar_box_texture.height * avatar_box_scale / 2)

        # drawing avatar
        avatar = self.window.client.avatar
        arcade.draw_texture_rectangle(texture=avatar, center_x=avatar_center_x, center_y=avatar_center_y,
                                      height=int(0.9 * avatar_box_texture.height * avatar_box_scale),
                                      width=int(0.9 * avatar_box_texture.height * avatar_box_scale))
        # drawing hud
        arcade.draw_texture_rectangle(center_x=avatar_center_x, center_y=avatar_center_y,
                                      width=int(avatar_box_texture.width * avatar_box_scale),
                                      height=int(avatar_box_texture.height * avatar_box_scale),
                                      texture=avatar_box_texture)

        nick_box_texture = load_texture('textures/NickBox_menu.png')
        nick_center_x = int(self.window.width - nick_box_texture.width * avatar_box_scale + int(
            nick_box_texture.width * avatar_box_scale / 2))
        nick_center_y = int(self.window.height - (nick_box_texture.height + avatar_box_texture.height)
                            * avatar_box_scale) + int(nick_box_texture.height * avatar_box_scale / 2)
        arcade.draw_texture_rectangle(nick_center_x, nick_center_y,
                                      int(nick_box_texture.width * avatar_box_scale),
                                      int(nick_box_texture.height * avatar_box_scale), texture=nick_box_texture)
        # drawing nick
        arcade.Text(text=self.window.client.name, multiline=False, bold=True, color=(10, 242, 255),
                    start_x=int(self.window.width - avatar_box_texture.width * avatar_box_scale / 2),
                    start_y=nick_center_y + int(0.12 * self.window.scale * nick_box_texture.height * avatar_box_scale),
                    anchor_y='center', anchor_x='center', font_size=int(24 * self.window.scale)).draw()

    def on_show_view(self):
        # Enable UIManager when view is shown to catch window events
        self.manager.enable()

    def on_hide_view(self):
        # Disable UIManager when view gets inactive
        self.manager.disable()
