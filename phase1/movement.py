from picrawler import Picrawler
from enum import StrEnum, auto
import time
from functools import wraps

class Movement(StrEnum):
    FORWARD = 'forward'
    BACKWARD = 'backward'
    TURN_LEFT = 'turn left'
    TURN_RIGHT = 'turn right'
    TURN_LEFT_ANGLE = 'turn left angle'
    TURN_RIGHT_ANGLE = 'turn right angle'

DEFAULT_SPEED = 85
MID_SPEED = 60

def pause_at_end(delay=0.5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            time.sleep(delay)
            return result
        return wrapper
    return decorator
# Angle with 1 step is 30 degrees, angle with 2 steps is 60 degrees

@pause_at_end(delay=1)
def move_angle_right(crawler: Picrawler, angle_steps: int, movement_steps: int, speed: int):
    crawler.do_action(Movement.TURN_RIGHT_ANGLE, angle_steps, speed)
    crawler.do_action(Movement.FORWARD, movement_steps, speed)

@pause_at_end(delay=1)
def observe(crawler: Picrawler):
    crawler.do_action(Movement.TURN_LEFT_ANGLE, 1, MID_SPEED)
    crawler.do_action(Movement.TURN_RIGHT_ANGLE, 1, MID_SPEED)
    crawler.do_action(Movement.TURN_RIGHT_ANGLE, 1, MID_SPEED)
    crawler.do_action(Movement.TURN_LEFT_ANGLE, 1, MID_SPEED)

def move_triangle_and_observe(crawler: Picrawler):
    crawler.do_action(Movement.FORWARD, 8, DEFAULT_SPEED)
    time.sleep(1)

    observe(crawler)
    move_angle_right(crawler, 4, 8, DEFAULT_SPEED)
    observe(crawler)
    move_angle_right(crawler, 4, 8, DEFAULT_SPEED)
    observe(crawler)

    
if __name__ == "__main__":
    crawler = Picrawler()
    move_triangle_and_observe(crawler)

