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

import random
from time import sleep
from formula import Formula
from game import Game
from random import randint
from events import StartFireEvent


def bot_start_thinking(game: Game, game_event_manager):
    """takes game object and local game  event manager, then waits random time, generates function
    using game object data and then adds local fire event with generated function"""

    sleep(randint(1, 5))
    formula = generate_function(game)
    game_event_manager.add_local_event(StartFireEvent(formula))


def generate_function(game: Game) -> Formula:
    """Takes game object as input and somehow calculates formula for
    currently active player. Takes list of obstacles from game.obstacles """
    formula = random.choice(
        ["3 cos (5x) / x", ' sin x', '5', 'x', 'abs(x)', '-x', 'exp(0.01x)', 'x%3', '(tan x) / 1000',
         '2sin (x) - (2sin(x)%0.5)'])
    return Formula(formula)
