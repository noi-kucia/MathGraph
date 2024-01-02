# MathGraph-combat
Welcome to MathGraph!

MathGraph is not typical game: here you must use mathematical equations to kill your enemies.
The game field represents coordinate plane where you have to draw graphs of functions, which represents some kind of 
bullet.
Your success depends only on your math skill and practice.<br>
Before you'll start the game, you should set the game parameters or leave the default ones.
<hr>

## let's take a closer look at the settings
<br>![settings](resources/lobby%20settings.png)
+ if `Marks on axes` is on, you will see auxiliary marks on the axes to make the game a bit easier
+ you can change `Marks frequency` parameter to adjust how often will be drawn auxiliary marks if graph units,<br>
if they are on of course.
+ `Friendly fire` switch allows you to set opportunity of killing your teammates
+ `Y axis limit` sets the graph highest y value (vertical edge). By changing this value you change the scale of whole<br>
graph, so `X axis limit` will be changed at the same time.
+ `game field width` sets the proportion of game field. While its height is constant, you can make the width less or<br>
more by cutting some part of graph. Thus, It influences the `X axis limit value`, but not the Y.<br>
You can even make the field square! 
+ `Time limit` sets the time which every player has to write equation and to shoot.
+ `obstacle frequency` shows how much obstacles will be spawned. Higher values correspond to higher difficulty of the<br>
game process, but they make it more interesting. If you are new, it's recommended to leave it on 20 or even decrease.
<br><br>
### At the bottom part of lobby you may see 2 teams and 3 buttons
![bottom](resources/lobby%20downside.png)
There cannot be more than 5 players in one team, therefore the maximum amount of players is 10.<br>
Red color of the nick emphasizes that it's you. In the right-top corner of players avatar you may see 2 buttons:
* double arrow is used to transfer a player to another team
* cross is used to kick player from lobby. Note, that you cannot kick yourself

At the bottom there are 3 buttons:
* `add bot` merely adds new bot to the lobby to the first not full team. Then you can transfer him to the other team,<br>
if you want so. If all team are full, bot won't be added
* `play game` starts new game with selected settings
* `exit` is used to exit lobby

# game interface
![game field](resources/game%20field.png)
In the center of the game field there are 2 axes arrows. If you turned on `Marks on axes`, you will see auxiliary marks<br>
without numbers on axes every `Marks frequency` units. Regardless is the auxiliary marks on, you'll see the marks with<br>
numbers on the ends of axes or on the last marks.<br><br>
Blue arrows represents alive players. Player with red nick is active now, you need to wait for your turn. When a player<br>
dies, his texture changes and nick becomes black.
<br><br>
![bottom](resources/game%20bottom%20panel.png)
At the center of the bottom panel you have input field to write your equation. It's big enough for almost all equations,<br>
but whenever necessary, it can be scrolled down. You can use combinations such as `ctrl+A`,`ctrl+X`,`ctrl+C` and `ctrl+V` 
when it's active (you must click it).<br><br>
On the left side from input field is located timer. When there are 15 seconds left, it starts blinking red.<br><br>
From the right side of input field you will see fire button, which will be active only when you are active player.<br><br>
`Skip vote` allows you to vote for change map, if it was generated bad. The map will be changed only when all alive players<br>
press this button.

# how to play?
So, first of all let's consider the game mechanic:<br>
You need to write a mathematical formula in input field. After you click the fire button, if your formula is correct,<br>
a red line will start to draw a graph of the function. If the graph touches player, it will kill them, but when it crosses over<br>
edge of graph or hits the obstacle, it stops and next alive player form opposite team will take turn.<br>

Your aim is to create such formula, which will avoid all obstacles on your way and touch as much enemies as possible.<br>
Be careful and try not to kill your teammates!<br>

If you hit the obstacle, it will be blown up and some part of them will be destroyed.<br>

The main feature of the game is function translation. What does it mean? It means, that function will be always coming out<br>
of the center of player sprite. To obtain such result, it will be lifted up or down. Thus, any constant values doesn't change<br>
anything. You need to think only about how function will raise after your position,and it's a bit hard for the first time.
![translation](resources/translation%20example.jpg)

Try to make some formulas, which grows only on certain parts and then combine them. For example `(abs(x-a)-abs(x-b))` 
will grow only on [a;b] and combining them you can make steps up or down:<br>
![example](resources/steps%20example.png)

Next, it's up to you, I won't spoiler ;)


# functions guide<br>

### available operators:

* '/'=':' - division
* '+' - addition
* '-' - subtraction
* '*' - multiplication
* '(' and ')' - parentheses
* '%' - modulo operator

### available functions:
*	abs() - absolute value
*	sqrt() = rt() - square root
*	exp() - exponent function = e^()
*	tan()=tg() - tangent
*	sin() - sinus
*	cos() - cosinus
*	log() = lg() - base  10 logarithm
*	ln - natural logarithm

### available constants:
*	e - Euler's number = 2.718281828459045
*	pi = 3.141592653589793238
	
### Syntax: 
Input is not case-sensitive. It means that `Pi = pi = PI`, `SQRT=sqrt`, `X=x `
but anyway I recommend  not to use caps.

You shouldn't type 'y=' or anything other than numbers, listed operators, functions or constants.

Two types of numbers are supported: 
integer and floating-point (divided via '.')
no complex numbers or anything else!

All operators have the same precedence as in math :
```
	highest ()
	  |	^
	  v  	*/:%
	 low    +,- 
```
Parentheses are optional, but recommended to avoid misinterpretations and to keep the formula 
readable. If a function doesn't have parentheses, it will take the left side expression until firs '+' or '-'
operator will be found (functions have the highest precedence only in relation to '+','-'):
* `sin 5*x+1 = sin(5*x)+1`
* `sqrt sin 5*x^2 +5 = sqrt(sin(5*x^2))+5`

You can skip the '*' sign between a number and any other object, but only when the number goes first :
* `5x=5*x`
* `23.1pi=23.1*pi`
* `2exp4(x+1) = 2*exp 4*(x+1)`

but 
* `x5≠x*5`
* `sin(x)3 ≠ sin(x)*3`
* `xx ≠ x*x` (`x x` also won't give `x*x` in result, because
firs `x` is not a number)

Or between parentheses: `(x-1)(x+sin x) = (x-1)*(x+sin x)`. In a similar way, the multiplication sign will be added 
between closing parenthesis and a name of other function or constant: `sin(x) sin(x) = sin(x)*sin(x)`.

White spaces, for instance a space, doesn't affect anything, so you can type 
`5*x` as well as `5 * x`, but the space sign is delimiter, so you must put it between constant or function names if
tere is no any other delimiters: `sin exp x` instead of `sinexpx` (I hope you don't plan to do so). Anyway it's better 
to use parentheses here to avoid mistakes `sin(exp(x))`. Also, `500 000` will
be interpreted as 2 numbers `500` and `0`. Number similarly can separate functions:<br> `sin4cos x = sin 4cos x =
sin(4cos x) = sin(4*cos x) = sin(4*cos(x))`

Using multiple or unnecessary operators is not allowed:
equations `+5`, `5**x`, `pi^^x`, `12--x`,`5+-3x` are incorrect 
but unary '-' is allowed as the first symbol and after '(' :
`-x`, `sin(-exp)` is OK, but `sin -5x` isn't.

':' is equal to '/'

All operators are left-associative, so operators with the same precedence will 
be considered from the left side:
`5x/3/2*pi = (((5*x)/3)/2)*pi`

There's a limit of 50000 for values of value during calculation, all numbers higher (or lower than -50000) will 
be interpreted as (-)50000 + random value [0;10), but you shouldn't notice that. `exp(10x)`for x>9 will always be ~5000.
To avoid an unpredictable behavior, I recommend abstain of using meaningless large multipliers. for instance, `100000000x`
will be rather horizontal line, than expected vertical because of large values was trimmed and the difference between 2 point 
was also annihilated. Same result may give addition off large number to any evaluation: `sin (5x) + 1000000000000`

Modulo operator returns remainder of Donald Knuth's floored division. It means that `-3.4 % 1` will return `0.6` because 
`-3.4-floor(-3.4) = -3.4-(-4) = 0.6`. It's quite hard operator, but very powerful. This operator makes a sharp jump,
using which you can go through obstacles, teammates or even enemies! 2 points are connected by red line, but it's not a
part of function, therefore this line hasn't collision:
![](resources/modulo%20jump%20example.png)
