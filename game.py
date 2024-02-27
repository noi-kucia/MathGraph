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
import math
import sys
import time
from threading import Timer

import pyglet.graphics

from UIFixedElements import *
from arcade import shape_list
from arcade import gui, geometry, color, load_texture, Text, SpriteList, View, Window
import arcade.types

from formula import Formula, TranslateError, ArgumentOutOfRange
from player import Player
import numpy as np
import pyclipper
import tripy
from shapely import Point, Polygon, LineString

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)


class Game:
    _proportion_x2y_max = 2.383

    def __init__(self, left_team: list = [], right_team: list = [], multiplayer: bool = False, axes_marked: bool = True,
                 marks_frequency: int = 5, proportion_x2y: float = 2.383,
                 y_edge: int = 16, friendly_fire_enable: bool = True, max_time_s: int = 150):

        self.multiplayer = multiplayer
        self.friendly_fire = friendly_fire_enable
        self.prev_active_player: Player = None
        self.max_time_s = max_time_s
        self.timer_time = max_time_s  # in-game timer time
        self.obstacles = []  # list of obstacle polygons
        self.obstacle_frequency = 20  # average obstacle frequency in %

        # marks on axes
        self.axes_marked = axes_marked
        self.marks_frequency = marks_frequency

        # graph (game field) settings:
        self.proportion_x2y = proportion_x2y  # height of graph is constant, but width = height*proportion_x2y
        self.y_edge = y_edge  # y value on the edge of graph
        self.x_edge = y_edge * proportion_x2y
        self.game_field_ratio = 1  # signifies the ratio of the game y axis to standard value (16)

        # players initializing
        self.players_sprites_list = SpriteList(use_spatial_hash=True)
        self.left_team = left_team
        self.right_team = right_team
        self.all_players = left_team + right_team
        self.active_player = None

        self.shooting = False
        self.formula_current_x = None  # when shooting, shows the relative x of the end of last segment
        self.formula = None  # Formula class object
        self.obstacles_color = ()
        self.obstacles_border_color = ()

        # list of formula segments
        self.formula_segments = shape_list.ShapeElementList()

    def create_obstacles(self):
        """generates obstacle on server machine using axes units coordinates,
        so these obstacles will be independent of screen resolution and before drawing
        must be scaled.

        These coordinates are common to all player and provides reference data to calculate
        collision."""

        self.obstacles.clear()  # deleting old obstacles
        max_polygons = int(self.obstacle_frequency * 0.8 * self.proportion_x2y / self._proportion_x2y_max)
        for i in range(
                int(max_polygons * (1 + random.uniform(-0.15, 0.15)))):  # creating +-15% from max_polygons times
            """generating new polygon"""
            while True:
                vertices = random.randint(3, 20)  # quantity of vertices in current polygon
                # polygons with more vertices normally will be bigger than other
                max_radius = int(random.uniform(1 * self.game_field_ratio,
                                                8 * self.game_field_ratio + 0.25 * self.game_field_ratio * vertices))

                # generating angles as part of 2 Pi radians:
                angle_sum = 0
                angles = []
                for _ in range(vertices):
                    angles.append(random.randint(35, 100))
                    angle_sum += angles[-1]
                for angle in range(vertices):
                    angles[angle] = angles[angle] / angle_sum

                point_list = []
                center_x = random.uniform(max_radius - self.x_edge, self.x_edge - max_radius)
                center_y = random.uniform(max_radius - self.y_edge, self.y_edge - max_radius)
                angle = 0
                last_scale = 0.75
                for part in angles:
                    angle -= 2 * math.pi * part
                    scale = random.uniform(0.25, 1)
                    scale = (scale + last_scale / 2) * 2 / 3  # making polygon more convex by smoothing angles
                    last_scale = scale
                    point_list.append(
                        (center_x + scale * max_radius * math.cos(angle),
                         center_y + scale * max_radius * math.sin(angle)
                         )
                    )
                polygon = Polygon(point_list)

                # checking polygon for collision with other obstacles
                is_intersecting = False
                for obstacle in self.obstacles:
                    if polygon.intersects(obstacle):
                        is_intersecting = True
                        break
                if is_intersecting:
                    continue

                # checking for collision with players
                # TODO: use shapely.geometry.box()
                for player in self.all_players:
                    player_polygon = Polygon([(player.x - player.player_size / 2,  # creating "hitbox" of player
                                       player.y + player.player_size / 2),
                                      (player.x + player.player_size / 2,
                                       player.y + player.player_size / 2),
                                      (player.x + player.player_size / 2,
                                       player.y - player.player_size / 2),
                                      (player.x - player.player_size / 2,
                                       player.y - player.player_size / 2)])
                    if player_polygon.intersects(polygon):
                        is_intersecting = True
                        break
                if is_intersecting:
                    continue
                break
            self.obstacles.append(polygon)

    def prepare(self):
        self.timer_time = self.max_time_s
        self.prev_active_player = None
        self.players_sprites_list = SpriteList(use_spatial_hash=True)
        self.shooting = False
        self.formula_current_x = None
        self.formula_segments = shape_list.ShapeElementList()
        self.all_players = self.left_team + self.right_team
        self.game_field_ratio = self.y_edge / 16

        # choosing obstacles color
        self.obstacles_color = random.choice(
            [(207, 14, 136), (37, 252, 13), (183, 16, 230), (255, 251, 10), (0, 255, 183)])
        self.obstacles_color += (60,)
        self.obstacles_border_color = self.obstacles_color + (150,)

        random.shuffle(self.left_team)
        random.shuffle(self.right_team)
        for player in self.right_team:
            player.left_player = False
            player.alive = True
        for player in self.left_team:
            player.left_player = True
            player.alive = True

    def is_game_end(self) -> bool:
        end = True
        for player in self.right_team:
            if player.alive:
                end = False
                break
        if end:
            return True
        end = True
        for player in self.left_team:
            if player.alive:
                end = False
        return end

    def get_next_player(self) -> Player:
        """returns Player object of the next player, who will be active.
        Next player is selected from opposite team always"""

        if self.active_player in self.left_team:
            next_team = self.right_team.copy()
        else:
            next_team = self.left_team.copy()

        try:
            player_index = next_team.index(self.prev_active_player) + 1
        except ValueError:
            player_index = 0
        while not next_team[player_index % len(next_team)].alive:
            player_index += 1

        new_active_player = next_team[player_index % len(next_team)]
        return new_active_player


class GameView(View):
    background = load_texture('textures/GameBackground_4k.jpg')
    panel_texture = load_texture('textures/bottom_panel_4k.jpg')

    def __init__(self, window: Window):
        super().__init__(window)
        self.translation_y_delta = None
        self.obstacle_border_batch_shapes = None
        self.obstacles_batch: pyglet.graphics.Batch() = None
        self.obstacle_body_batch_shapes = None
        self.formula_field: AdvancedUIInputText = None
        self.time_text: Text = None
        self.game_field_objects = shape_list.ShapeElementList()  # contains all static shape elements of the interface
        self.nick_names = []  # list to keep nick Text objects

        if not window.lobby.game:
            raise Exception

        self.game = window.lobby.game


        # graph edges coordinates
        self.graph_top_edge = window.GRAPH_TOP_EDGE
        self.graph_bottom_edge = window.GRAPH_BOTTOM_EDGE
        self.graph_left_edge = int(
            window.SCREEN_WIDTH - (
                    self.graph_top_edge - self.graph_bottom_edge) * self.game.proportion_x2y) // 2
        self.graph_right_edge = window.SCREEN_WIDTH - self.graph_left_edge

        self.graph_width = self.graph_right_edge - self.graph_left_edge
        self.graph_height = self.graph_top_edge - self.graph_bottom_edge
        self.px_per_unit = self.graph_width / self.game.x_edge / 2  # shows how much pixels are in 1 game unit

        self.graph_x_center = (self.graph_right_edge + self.graph_left_edge) / 2
        self.graph_y_center = (self.graph_top_edge + self.graph_bottom_edge) / 2

        # panel edges
        self.panel_top_edge = self.graph_bottom_edge - 5
        self.formula_input_height = int(self.panel_top_edge - 95 * self.window.scale)
        self.formula_input_width = window.SCREEN_WIDTH / 2.88

        # to keep text objects
        self.text_to_draw = []

        # creating sprites of players
        for player in self.game.all_players:
            player.create_sprite(self)

        # adding UI
        self.manager = gui.UIManager()  # for all gui elements
        self.add_ui()

        # adding game event manager object
        from events import GameEventManager
        self.game_event_manager = GameEventManager()

        if not self.game.multiplayer:
            # randomly choosing active player
            active_player = random.choice(self.game.all_players)
            from events import ActivePlayerChangeEvent
            self.game_event_manager.add_local_event(ActivePlayerChangeEvent(active_player))

        # generating obstacles
        self.game.create_obstacles()
        self.create_obstacles_batch()

        # adding thread to timer func
        self.game.timer_time = self.game.max_time_s
        self.timer = Timer(1, self.time_tick)
        self.timer.start()

    def time_tick(self):
        self.game.timer_time -= 1
        self.timer = Timer(1, self.time_tick)
        self.timer.start()

    def on_show_view(self):
        self.manager.enable()

    def on_hide_view(self):
        self.manager.disable()
        if self.timer:
            self.timer.cancel()

    def add_ui(self):
        """There is creating of all IU:
        buttons, input for the formula and other"""
        window = self.window

        # adding formula input field
        self.formula_field = AdvancedUIInputText(text='formula', font_size=int(18 * window.scale),
                                                 text_color=color.WHITE,
                                                 multiline=True, width=self.formula_input_width,
                                                 height=self.formula_input_height)
        self.formula_field.caret.move_to_point(4000, 0)  # moving caret to the end
        self.formula_field.layout.document.set_style(0, -1,
                                                     {"wrap": "char"})  # setting line feed to feed after every char
        self.formula_field._active = True  # making it active by default

        formula_anchor = gui.UIAnchorLayout()
        formula_anchor.add(self.formula_field, anchor_x='center', anchor_y='bottom', align_y=int(60 * window.scale))

        # adding fire button
        fire_button_texture = load_texture('textures/fire_button.png')
        fire_button_texture_hovered = load_texture('textures/fire_button_hovered.png')
        fire_button_texture_disabled = load_texture('textures/fire_button_disabled.png')
        fire_button_scale = 0.5 * window.scale

        fire_button_texture_pressed = load_texture('textures/fire_button_pressed.png')

        self.fire_button = FixedUITextureButton(texture=fire_button_texture,
                                                texture_hovered=fire_button_texture_hovered,
                                                texture_pressed=fire_button_texture_pressed,
                                                texture_disabled=fire_button_texture_disabled, scale=fire_button_scale)
        self.fire_button.on_click = self.fire

        # adding exit button
        quit_button_texture = load_texture('textures/LobbyExitButton.png')
        quit_button_texture_pressed = load_texture('textures/LobbyExitButton_hovered.png')
        quit_button_scale = 0.65 * window.scale
        quit_button = FixedUITextureButton(texture=quit_button_texture,
                                           width=quit_button_texture.width * quit_button_scale,
                                           height=quit_button_texture.height * quit_button_scale,
                                           texture_hovered=quit_button_texture_pressed)
        quit_button.on_click = self.game_quit  # adding skip map checkbox(also button) and button

        checkbox_scale = 0.24 * window.scale
        checkbox_pressed_texture = load_texture('textures/square_checkBox_pressed.png')
        checkbox_empty_texture = load_texture('textures/square_checkBox_empty.png')
        vote_button_texture = load_texture('textures/skip_vote_button.png')
        vote_button_texture_hovered = load_texture('textures/skip_vote_button_hovered.png')
        vote_button_scale = 0.675 * window.scale

        # adding skip vote
        skip_checkbox = FixedUITextureToggle(on_texture=checkbox_pressed_texture,
                                             off_texture=checkbox_empty_texture,
                                             value=False, width=checkbox_empty_texture.width * checkbox_scale,
                                             height=checkbox_empty_texture.height * checkbox_scale)
        vote_button = FixedUITextureButton(width=int(vote_button_texture.width * vote_button_scale),
                                           height=int(vote_button_texture.height * vote_button_scale),
                                           texture=vote_button_texture,
                                           texture_hovered=vote_button_texture_hovered)

        @vote_button.event("on_click")
        def vote(event):
            skip_checkbox.value = not skip_checkbox.value
            self.skip_vote()

        @skip_checkbox.event("on_change")
        def vote(event):
            self.skip_vote()

        ui_anchor = gui.UIAnchorLayout()
        ui_anchor.add(formula_anchor)
        ui_anchor.add(skip_checkbox, anchor_x='left', anchor_y='bottom',
                      align_x=int(30 * window.scale),
                      align_y=int(50 * window.scale + quit_button_texture.height * quit_button_scale))
        ui_anchor.add(vote_button, anchor_x='left', anchor_y='bottom',
                      align_x=int(45 * window.scale + checkbox_empty_texture.width * checkbox_scale),
                      align_y=int(50 * window.scale + quit_button_texture.height * quit_button_scale))
        ui_anchor.add(self.fire_button, anchor_x='right',
                      align_x=int(-self.window.width / 5.45 - window.width / 2 - 25 * window.scale),
                      anchor_y='bottom',
                      align_y=int(
                          (self.panel_top_edge - fire_button_texture.height * fire_button_scale) / 2
                      ) + 10 * window.scale
                      )
        ui_anchor.add(quit_button, anchor_x='left', anchor_y='bottom', align_y=int(25 * window.scale),
                      align_x=int(30 * window.scale))
        self.manager.add(ui_anchor)

        # adding timer Text object
        self.time_text = Text(
            text='{:0>2d}:{:0>2d}'.format(window.lobby.game.timer_time // 60, window.lobby.game.timer_time % 60),
            anchor_x='center', anchor_y='center', multiline=False, color=(128, 245, 255),
            start_x=int(window.width - 210 * window.scale), start_y=int(110 * window.scale),
            font_size=int(72 * window.scale)
        )

    def skip_vote(self):
        if not self.game.multiplayer:  # immediately change map if game it's solo game
            if self.timer:
                self.timer.cancel()
            start_new_game(self.window.lobby, self.window)

    def game_quit(self, event):
        # TODO: customize message box, make font bigger and use some UI background
        message_box = gui.UIMessageBox(
            width=400,
            height=300,
            message_text='Are you sure you wanna leave the game?',
            buttons=["Yes", "No"],
        )
        self.manager.add(message_box)

        @message_box.event("on_action")
        def on_action(event: gui.UIOnActionEvent):
            if event.action == 'Yes':
                if self.timer:
                    self.timer.cancel()
                from lobby import LobbyView
                view = LobbyView(self.window)
                self.window.show_view(view)

    def fire(self, event):
        """This function activates when user press fire button"""
        user_formula = self.formula_field.text
        game = self.window.lobby.game
        if game.active_player.client != self.window.client:  # cannot shoot if not active
            return
        if game.shooting:  # cannot shoot until previous shoot end
            return
        try:
            formula = Formula(user_formula)
        except TranslateError:
            self.send_message('Something went wrong during translation,\nformula is not correct!')
            return
        from events import StartFireEvent
        self.game_event_manager.add_local_event(StartFireEvent(formula))

    def send_message(self, text):
        message_box = gui.UIMessageBox(
            width=300,
            height=200,
            message_text=text,
            buttons=["Ok"],
        )
        self.manager.add(message_box)

    def kill_player(self, player: Player):
        """changing player texture to dead,
        making him inactive in game if this is not active player"""
        game = self.window.lobby.game
        if player == game.active_player:
            return None  # cannot kill himself
        if not player.alive:
            return None  # cannot kill dead player
        player.set_dead_texture()
        player.alive = False

    def game_finish(self):
        self.timer.cancel()
        from lobby import LobbyView
        view = LobbyView(self.window)
        self.window.show_view(view)

    def obstacle_hit(self, obstacle_index, point: Point):
        """This method takes obstacle index from game.obstacles
        list and clipping it, making blow effect. It works using
        pyclipper library and there is no documentation at all, so
        it's a miracle that it works. Pls, don't touch the part with pyclipper.

        clipper is the polygon of "blow", it's a bit randomized and has given size as radius"""

        game = self.game
        float_precision = 0.01 / game.game_field_ratio  # as pyclipper cannot work on floats, all integers will be
        # divided by this precision before clipping and all new polygons will be multiplied by it again then
        blow_radius = 1.5 * game.game_field_ratio / float_precision
        obstacle = game.obstacles[obstacle_index]
        obstacle = [(x / float_precision, y / float_precision) for x, y in obstacle]

        # deleting previous obstacle shapes from batch
        self.obstacle_body_batch_shapes.pop(obstacle_index)
        self.obstacle_border_batch_shapes.pop(obstacle_index)
        game.obstacles.pop(obstacle_index)  # deleting old obstacle game object

        # generating clipping polygon
        angle_angle_sum = 0
        angles = []
        vertices = 8
        for _ in range(vertices):
            angles.append(random.randint(85, 100))
            angle_angle_sum += angles[-1]
        for angle in range(vertices):
            angles[angle] = angles[angle] / angle_angle_sum

        center_x = point.x / float_precision
        center_y = point.y / float_precision
        clipper = []
        angle = 0
        for part in angles:
            angle += 2 * math.pi * part
            clipper.append(
                (center_x + blow_radius * math.cos(angle),
                 center_y + blow_radius * math.sin(angle)
                 )
            )

        # calculating new obstacle(s)
        pc = pyclipper.Pyclipper()
        pc.AddPath(obstacle, pyclipper.PT_CLIP, True)
        pc.AddPath(clipper, pyclipper.PT_SUBJECT, True)
        if not pc.Execute(pyclipper.CT_DIFFERENCE):  # if whole clipping polygon is inside subject
            return
        pc.Clear()
        pc.AddPath(obstacle, pyclipper.PT_SUBJECT, True)
        pc.AddPath(clipper, pyclipper.PT_CLIP, True)
        new_obstacles = pc.Execute(pyclipper.CT_DIFFERENCE, pyclipper.PFT_EVENODD)

        for obstacle in new_obstacles:
            if not obstacle:
                continue
            # translating vertices coordinates back to the game units
            obstacle = [(x * float_precision, y * float_precision) for x, y in obstacle]
            game.obstacles.append(obstacle)  # adding new obstacle
            self.add_batch_obstacle(obstacle)  # creating new shapes

    def on_update(self, delta_time=1. / 60):
        window = self.window
        game = window.lobby.game

        self.game_event_manager.listen_game_events(game)  # receiving new events to be executed
        try:
            self.game_event_manager.execute_events(self)  # executing events locally
        except Exception as e:
            print(e)

        if game.shooting:
            """when the game shooting event is active, a part of the formula is drawn each frame.
            This process is local to performance needs and to alleviate server's load,
            so may vary a bit if players have  different screen resolutions.
            
            Then, if the game is multiplayer, a server will send its version of the  result of the shoot like who 
            was killed, which obstacles have been damaged and so on"""

            shooter_right: bool = game.active_player in game.right_team
            segments_per_frame = int(12 * self.window.scale)
            x_step_px = 0.5 * window.scale
            x_step = x_step_px / self.px_per_unit * (-1 if shooter_right else 1)  # step in axis units ( regards the sign )
            point_list = []

            try:
                # evaluating the coordinates of segment points
                for _ in range(segments_per_frame + 1):
                    point_y = game.formula.evaluate(game.formula_current_x) + self.translation_y_delta
                    point_list.append((game.formula_current_x, point_y))
                    game.formula_current_x += x_step
                segment = LineString(point_list)
                game.formula_current_x -= x_step  # decreasing the value, as it was increased 1 more time at the end of segment

                # translating and adding this segment to the screen to be drawn
                screen_points = [(self.graph_x_center + self.px_per_unit * x, self.graph_y_center + self.px_per_unit * y) for x, y in point_list]
                game.formula_segments.append(shape_list.create_line_strip(point_list=screen_points, color=color.RED,
                                                                          line_width=1 * window.scale))

                # checking for collision with obstacles
                for obstacle_index in range(len(game.obstacles)):
                    obstacle = Polygon(game.obstacles[obstacle_index])
                    intersections = segment.intersection(obstacle)
                    if intersections:
                        first_collision_point = None
                        match intersections.geom_type:
                            case 'LineString':
                                first_collision_point = Point(intersections.coords[-1] if shooter_right else intersections.coords[0])
                            case 'MultiLineString':
                                for line in intersections.geoms:
                                    if not first_collision_point:
                                        first_collision_point = Point(line.coords[-1] if shooter_right else line.coords[0])
                                    elif shooter_right and line.coords[-1][0] > first_collision_point.x:
                                        first_collision_point = Point(line.coords[-1])
                                    elif not shooter_right and line.coords[0][0] < first_collision_point.x:
                                        first_collision_point = Point(line.coords[0])
                            case 'Point':
                                first_collision_point = intersections
                            case _:
                                print('\n\nunknown geometry: ', _)
                        self.obstacle_hit(obstacle_index, first_collision_point)
                        self.stop_shooting()
                        return

                # checking for collision with players
                active_team = game.left_team if game.active_player in game.left_team else game.right_team
                for player in game.all_players:
                    if player == game.active_player:
                        continue
                    if player in active_team and not game.friendly_fire :
                        continue
                    if segment.intersects(player.hitbox):
                        self.kill_player(player)
                        continue

                # checking for crossing over vertical borders
                if abs(point_list[-1][1]) >= game.y_edge:
                    self.stop_shooting()
                    return

                # checking for crossing over horizontal borders
                if abs(game.formula_current_x) >= game.x_edge:
                    self.stop_shooting()
                    return

            except Exception as exception:
                self.stop_shooting()
                if exception == ZeroDivisionError:
                    print('Zero dividing found! Shoot stopped!')
                elif exception == ArgumentOutOfRange:
                    print('Argument error! Shoot stopped!')
                else:
                    print('some error occurred!', exception)

    def stop_shooting(self):
        game = self.game
        self.on_draw()  # drawing last segment with overlapping
        time.sleep(1 / 60)
        game.shooting = False
        game.formula = None
        game.formula_current_x = None
        game.formula_segments = None
        if not game.multiplayer:
            from events import GameEndEvent, ActivePlayerChangeEvent
            if game.is_game_end():
                self.game_event_manager.add_local_event(GameEndEvent())
                self.game_event_manager.execute_events(self)
                return
            next_player = game.get_next_player()
            self.game_event_manager.add_local_event(ActivePlayerChangeEvent(next_player))

    def on_draw(self):
        self.clear()
        arcade.start_render()
        self.game_field_draw()
        for text in self.text_to_draw:
            text.draw()
        self.bottom_panel_draw()
        self.obstacles_draw()
        if self.window.lobby.game.formula_segments:  # if there is a formula to draw
            self.draw_formula()
        self.players_draw()
        self.manager.draw()

        # timer drawing
        timer_time = self.window.lobby.game.timer_time
        self.time_text.text = '{:0>2d}:{:0>2d}'.format(timer_time // 60, timer_time % 60)
        # making timer blink red-blue on the last 15 seconds
        self.time_text.color = (128, 245, 255) if (timer_time > 15 or not timer_time % 2) else (245, 10, 10)
        self.time_text.draw()

        arcade.finish_render()

    def create_obstacles_batch(self):
        """translates from axes units to pixels and creates local batch of obstacle shapes"""
        self.obstacles_batch = pyglet.graphics.Batch()  # creating new batch
        self.obstacle_body_batch_shapes = []
        self.obstacle_border_batch_shapes = []
        for polygon in self.game.obstacles:
            self.add_batch_obstacle(polygon)

    def add_batch_obstacle(self, polygon):
        """Takes a polygon on input in game units,
         translates to the pixels and adds it to the local obstacle batch. Also creates border for it"""

        obstacle = []
        border = []

        # translating into pixel units and moving to appropriate position
        polygon = [(x * self.px_per_unit + self.graph_x_center, y * self.px_per_unit + self.graph_y_center)
                   for x, y in polygon.exterior.coords]

        # creating obstacle body from triangles
        triangles = tripy.earclip(polygon)
        for tr in triangles:
            obstacle.append(pyglet.shapes.Triangle(tr[0][0], tr[0][1], tr[1][0], tr[1][1], tr[2][0], tr[2][1],
                                                   self.game.obstacles_color, batch=self.obstacles_batch))
        self.obstacle_body_batch_shapes.append(obstacle)

        # creating obstacle border
        last_point = polygon[-1]
        for point in polygon:
            border.append(pyglet.shapes.Line(last_point[0], last_point[1], point[0], point[1],
                                             width=int(2 * self.window.scale),
                                             color=self.game.obstacles_border_color, batch=self.obstacles_batch))
            last_point = point
        self.obstacle_border_batch_shapes.append(border)

    def obstacles_draw(self):
        batch = self.obstacles_batch
        batch.draw()

    def players_draw(self):
        game = self.game
        game.players_sprites_list.draw()

        # drawing nicknames
        for player in (game.right_team + game.left_team):
            player.nick.bold = False
            if player == game.active_player:
                player.nick.color = (212, 28, 15)
                player.nick.bold = True
            elif not player.alive:
                player.nick.color = color.BLACK
            else:
                player.nick.color = (255, 255, 255)
            player.nick.draw()

            # ### hitbox drawing
            # center_x = player.x * self.px_per_unit + self.graph_x_center
            # center_y = player.y * self.px_per_unit + self.graph_y_center
            # radius = player.player_size*0.9/2 * self.px_per_unit
            # arcade.draw_circle_filled(center_x, center_y, radius, (255, 0, 0, 200))

    def draw_formula(self):
        self.window.lobby.game.formula_segments.draw()

    def bottom_panel_draw(self):
        window = self.window

        # panel drawing
        arcade.draw_lrwh_rectangle_textured(0, 0, window.width, self.panel_top_edge, texture=self.panel_texture)

    def game_field_draw(self):
        game = self.window.lobby.game
        window = self.window

        arcade.draw_lrwh_rectangle_textured(0, 0, window.SCREEN_WIDTH, window.SCREEN_HEIGHT,
                                            self.background)  # background image

        if self.game_field_objects:  # if objects have been already created
            self.game_field_objects.draw()
            return

        # else creating new
        max_y_value = game.y_edge
        max_x_value = max_y_value * game.proportion_x2y

        graph_lines_color_hex = window.GRAPH_LINES_COLOR_HEX  # color of arrows and marks

        # adding graph field and edges:
        self.game_field_objects.append(
            shape_list.create_rectangle_filled(center_x=int((self.graph_left_edge + self.graph_right_edge) / 2),
                                               center_y=int((self.graph_top_edge + self.graph_bottom_edge) / 2),
                                               width=self.graph_width,
                                               height=self.graph_height,
                                               color=(11, 1, 18, 200)
                                               )
        )
        self.game_field_objects.append(
            shape_list.create_rectangle_outline(
                center_x=int((self.graph_left_edge + self.graph_right_edge) / 2),
                center_y=int((self.graph_top_edge + self.graph_bottom_edge) / 2),
                width=self.graph_width + 3,
                height=self.graph_height + 3,
                color=color.AERO_BLUE, border_width=3
            )
        )

        # adding vertical arrow
        self.game_field_objects.append(
            shape_list.create_line(
                start_x=self.graph_x_center, start_y=self.graph_bottom_edge, end_x=self.graph_x_center,
                end_y=self.graph_top_edge, color=arcade.types.Color.from_hex_string(graph_lines_color_hex)
            )
        )
        self.game_field_objects.append(
            shape_list.create_line(
                start_x=self.graph_x_center - 7, start_y=self.graph_top_edge - 10, end_x=self.graph_x_center,
                end_y=self.graph_top_edge, color=arcade.types.Color.from_hex_string(graph_lines_color_hex),
                line_width=1
            )
        )
        self.game_field_objects.append(
            shape_list.create_line(
                start_x=self.graph_x_center + 7, start_y=self.graph_top_edge - 10, end_x=self.graph_x_center,
                end_y=self.graph_top_edge, color=arcade.types.Color.from_hex_string(graph_lines_color_hex),
                line_width=1
            )
        )

        # adding horizontal arrow
        self.game_field_objects.append(
            shape_list.create_line(
                start_x=self.graph_left_edge, start_y=self.graph_y_center, end_x=self.graph_right_edge,
                end_y=self.graph_y_center, color=arcade.types.Color.from_hex_string(graph_lines_color_hex)
            )
        )
        self.game_field_objects.append(
            shape_list.create_line(
                start_x=self.graph_right_edge - 10, start_y=self.graph_y_center + 7, end_x=self.graph_right_edge,
                end_y=self.graph_y_center, color=arcade.types.Color.from_hex_string(graph_lines_color_hex)
            )
        )
        self.game_field_objects.append(
            shape_list.create_line(
                start_x=self.graph_right_edge - 10, start_y=self.graph_y_center - 7, end_x=self.graph_right_edge,
                end_y=self.graph_y_center, color=arcade.types.Color.from_hex_string(graph_lines_color_hex)
            )
        )

        """drawing marks on axes if enabled"""
        # minimal offset from graph edges in x/y values
        x_delta = 0.9
        y_delta = 0.9

        marks_frequency = game.marks_frequency
        if game.axes_marked:
            if marks_frequency >= int(max_x_value - x_delta) + 1:  # if no marks will be drawn on x-axis
                last_x = x_mark = max_x_value - x_delta
                x_coordinate = self.graph_width / 2 / max_x_value * x_mark + self.graph_x_center
                self.game_field_objects.append(
                    shape_list.create_line(
                        start_x=x_coordinate, start_y=self.graph_y_center - 6,
                        end_x=x_coordinate, end_y=self.graph_y_center + 6,
                        color=arcade.types.Color.from_hex_string(graph_lines_color_hex), line_width=2
                    )
                )
                x_coordinate = self.graph_x_center - self.graph_width / 2 / max_x_value * x_mark
                self.game_field_objects.append(
                    shape_list.create_line(
                        start_x=x_coordinate, start_y=self.graph_y_center - 6,
                        end_x=x_coordinate, end_y=self.graph_y_center + 6,
                        color=arcade.types.Color.from_hex_string(graph_lines_color_hex), line_width=2
                    )
                )
            else:
                for x_mark in np.arange(marks_frequency, int(max_x_value - x_delta) + 1, marks_frequency):
                    last_x = x_mark
                    x_coordinate = self.graph_width / 2 / max_x_value * x_mark + self.graph_x_center
                    self.game_field_objects.append(
                        shape_list.create_line(
                            start_x=x_coordinate, start_y=self.graph_y_center - 6,
                            end_x=x_coordinate, end_y=self.graph_y_center + 6,
                            color=arcade.types.Color.from_hex_string(graph_lines_color_hex), line_width=2
                        )
                    )
                    x_coordinate = self.graph_x_center - self.graph_width / 2 / max_x_value * x_mark
                    self.game_field_objects.append(
                        shape_list.create_line(
                            start_x=x_coordinate, start_y=self.graph_y_center - 6,
                            end_x=x_coordinate, end_y=self.graph_y_center + 6,
                            color=arcade.types.Color.from_hex_string(graph_lines_color_hex), line_width=2
                        )
                    )

            if marks_frequency >= \
                    (1 + int(max_y_value) if (max_y_value - int(max_y_value) > y_delta) else int(
                        max_y_value - y_delta)):  # if no marks will be drawn on y-axis

                last_y = y_mark = int(max_y_value - y_delta)
                y_coordinate = self.graph_height / 2 / max_y_value * y_mark + self.graph_y_center
                self.game_field_objects.append(
                    shape_list.create_line(
                        start_x=self.graph_x_center - 6, start_y=y_coordinate,
                        end_x=self.graph_x_center + 6, end_y=y_coordinate,
                        color=arcade.types.Color.from_hex_string(graph_lines_color_hex), line_width=2
                    )
                )
                y_coordinate = self.graph_y_center - self.graph_height / 2 / max_y_value * y_mark
                self.game_field_objects.append(
                    shape_list.create_line(
                        start_x=self.graph_x_center - 6, start_y=y_coordinate,
                        end_x=self.graph_x_center + 6, end_y=y_coordinate,
                        color=arcade.types.Color.from_hex_string(graph_lines_color_hex), line_width=2
                    )
                )
            else:
                for y_mark in \
                        np.arange(marks_frequency,
                                  (1 + int(max_y_value) if (max_y_value - int(max_y_value) < y_delta) else
                                  int(max_y_value - y_delta)), marks_frequency):
                    last_y = y_mark
                    y_coordinate = self.graph_height / 2 / max_y_value * y_mark + self.graph_y_center
                    self.game_field_objects.append(
                        shape_list.create_line(
                            start_x=self.graph_x_center - 6, start_y=y_coordinate,
                            end_x=self.graph_x_center + 6, end_y=y_coordinate,
                            color=arcade.types.Color.from_hex_string(graph_lines_color_hex), line_width=2
                        )
                    )
                    y_coordinate = self.graph_y_center - self.graph_height / 2 / max_y_value * y_mark
                    self.game_field_objects.append(
                        shape_list.create_line(
                            start_x=self.graph_x_center - 6, start_y=y_coordinate,
                            end_x=self.graph_x_center + 6, end_y=y_coordinate,
                            color=arcade.types.Color.from_hex_string(graph_lines_color_hex), line_width=2
                        )
                    )
        else:
            # if axes are not marked, drawing only marks on edges with numbers
            x_mark = int(max_x_value - x_delta)
            y_mark = int(max_y_value) if (max_y_value - int(max_y_value) > y_delta) else int(max_y_value - y_delta)
            last_x = x_mark

            # x marks
            x_coordinate = self.graph_width / 2 / max_x_value * x_mark + self.graph_x_center
            self.game_field_objects.append(
                shape_list.create_line(
                    start_x=x_coordinate, start_y=self.graph_y_center - 6,
                    end_x=x_coordinate, end_y=self.graph_y_center + 6,
                    color=arcade.types.Color.from_hex_string(graph_lines_color_hex), line_width=2
                )
            )
            x_coordinate = self.graph_x_center - self.graph_width / 2 / max_x_value * x_mark
            self.game_field_objects.append(
                shape_list.create_line(
                    start_x=x_coordinate, start_y=self.graph_y_center - 6,
                    end_x=x_coordinate, end_y=self.graph_y_center + 6,
                    color=arcade.types.Color.from_hex_string(graph_lines_color_hex), line_width=2
                )
            )

            # y marks
            last_y = y_mark
            y_coordinate = self.graph_height / 2 / max_y_value * y_mark + self.graph_y_center
            self.game_field_objects.append(
                shape_list.create_line(
                    start_x=self.graph_x_center - 6, start_y=y_coordinate,
                    end_x=self.graph_x_center + 6, end_y=y_coordinate,
                    color=arcade.types.Color.from_hex_string(graph_lines_color_hex), line_width=2
                )
            )
            y_coordinate = self.graph_y_center - self.graph_height / 2 / max_y_value * y_mark
            self.game_field_objects.append(
                shape_list.create_line(
                    start_x=self.graph_x_center - 6, start_y=y_coordinate,
                    end_x=self.graph_x_center + 6, end_y=y_coordinate,
                    color=arcade.types.Color.from_hex_string(graph_lines_color_hex), line_width=2
                )
            )

        # adding numbers to the last marks
        x_coordinate = self.graph_width / 2 / max_x_value * last_x + self.graph_x_center
        if self.graph_right_edge - x_coordinate < 15 * window.scale:
            x_coordinate = self.graph_right_edge - 15 * window.scale
        self.text_to_draw.append(Text(str(int(last_x)), x_coordinate, self.graph_y_center - 8 * window.scale,
                                      arcade.types.Color.from_hex_string(graph_lines_color_hex),
                                      font_size=12 * window.scale,
                                      anchor_x='center', anchor_y='top'))
        x_coordinate = self.graph_x_center - self.graph_width / 2 / max_x_value * last_x
        if x_coordinate - self.graph_left_edge < 15 * window.scale:
            x_coordinate = self.graph_left_edge + 15 * window.scale
        self.text_to_draw.append(Text(str(-int(last_x)), x_coordinate, self.graph_y_center - 8 * window.scale,
                                      arcade.types.Color.from_hex_string(graph_lines_color_hex),
                                      font_size=12 * window.scale,
                                      anchor_x='center', anchor_y='top'))
        y_coordinate = self.graph_height / 2 / max_y_value * last_y + self.graph_y_center
        if self.graph_top_edge - y_coordinate < 8 * window.scale:
            y_coordinate = self.graph_top_edge - 8 * window.scale
        self.text_to_draw.append(Text(str(int(last_y)), self.graph_x_center - 8 * window.scale, y_coordinate,
                                      arcade.types.Color.from_hex_string(graph_lines_color_hex),
                                      font_size=12 * window.scale,
                                      anchor_y='center', anchor_x='right'))
        y_coordinate = self.graph_y_center - self.graph_height / 2 / max_y_value * last_y
        if y_coordinate - self.graph_bottom_edge < 8 * window.scale:
            y_coordinate = self.graph_bottom_edge + 8 * window.scale
        self.text_to_draw.append(Text(str(-int(last_y)), self.graph_x_center - 8 * window.scale, y_coordinate,
                                      arcade.types.Color.from_hex_string(graph_lines_color_hex),
                                      font_size=12 * window.scale,
                                      anchor_y='center', anchor_x='right'))

        # drawing for the first time, when added all elements
        self.game_field_objects.draw()
        for text in self.text_to_draw:
            text.draw()


def start_new_game(lobby, window):
    game = lobby.game
    game.prepare()
    view = GameView(window)
    window.show_view(view)
