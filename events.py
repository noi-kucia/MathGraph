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
from threading import Timer
from typing import List
from game import Game, GameView
from player import Player


class GameEvent:
    __action: str = ""  # declares the type of the event

    def __init__(self, action: str):
        self.set_action(action)

    def set_action(self, action: str):
        self.__action = action

    def get_action(self) -> str:  # get the type of the event
        return self.__action


class ActivePlayerChangeEvent(GameEvent):
    __new_active_player: Player

    def __init__(self, active_player: Player):
        super().__init__("ActivePlayerChange")
        assert active_player, "new active player need to be specified!"
        self.__new_active_player = active_player

    def get_player(self) -> Player:
        return self.__new_active_player


class GameEndEvent(GameEvent):

    def __init__(self):
        super().__init__(action="GameEnd")


class EventManager:
    """contains queue of the events which can be executed using execute_events"""

    def __init__(self):
        self.events: List[GameEvent] = []

    def execute_events(self, **kwargs):
        """override this function in dependence of events type"""
        pass

    def dispatchEvent(event: GameEvent, game: Game):
        """dispatches some event to the dedicated server"""

    def add_local_event(self, event: GameEvent):
        if event:
            self.events.append(event)


class GameEventManager(EventManager):

    def listen_game_events(self, game: Game):
        """Retrieving both local and dedicated events and saves it inside Manager"""

        if game.multiplayer:
            # receiving data from dedicated server
            pass
            return []

        # if game is local, creating events here

        # Timer events
        if game.timer_time <= 0:

            if game.is_game_end():
                self.add_local_event(GameEndEvent())
            else:

                new_active_player = game.get_next_player()
                self.add_local_event(ActivePlayerChangeEvent(new_active_player))

                # when bot becomes an active player we're starting thread for him and waiting for shoot event
                if new_active_player.computer_player:
                    pass

    def execute_events(self, view: GameView):
        """executes all events from internal queue and deletes them"""

        if not self.events:
            return

        game = view.game
        while len(self.events) != 0:

            event = self.events.pop()
            match event.get_action():

                case "ActivePlayerChange":
                    view.timer.cancel()  # stopping timer

                    # changing previous and active players
                    game.prev_active_player = game.active_player
                    game.active_player = game.get_next_player()

                    # changing fire button condition
                    if game.active_player.client == view.window.client:
                        view.fire_button.disabled = False
                    else:
                        view.fire_button.disabled = True

                    self.add_local_event(GameEvent("TimerReset"))  # adding timer reset action to the queue

                case "TimerReset":
                    # resetting timer time to the maximum value and starting new Timer thread
                    game.timer_time = game.max_time_s
                    view.timer = Timer(1, view.time_tick)
                    view.timer.start()

                case "GameEnd":
                    view.game_finish()

                case _:
                    print("unknown event type:", event.get_action())
