import door
import time

door = door.Door()
while True:
    door.update_state()
    print('state: ' + str(door.state.name))
    time.sleep(0.5)
