import door
import time

door = door.Door()
while True:
    door.update_state()
    time.sleep(0.5)
