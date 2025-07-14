from .mouse import (left_down, left_up, left_click,
                    right_down, right_up, right_click,
                    side1_down, side1_up, side1_click,
                    side2_down, side2_up, side2_click,
                    move_relative, move_absolute, wheel_scroll)

from .keyboard import (key_down, key_up, key_click, key_combination)

__all__ = [
    'left_down', 'left_up', 'left_click',
    'right_down', 'right_up', 'right_click',
   'side1_down','side1_up','side1_click',
   'side2_down','side2_up','side2_click',
   'move_relative','move_absolute', 'wheel_scroll',
    'key_down', 'key_up', 'key_click', 'key_combination'
]