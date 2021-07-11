import time
import asyncio
from enum import Flag, auto
from DS3225 import DS3225       # モーター
from RC522 import RC522         # RFIDリーダー
from SR04 import SR04           # 超音波距離センサ
from LEAD_SWITCH import LEAD_SWITCH
from LINE import LINE
from google_home import google_home

UNLOCKED_DEG = 175
LOCKED_DEG = 85
UNLOCKED_TIME = 10
DISTANCE = 50
NOTIFTY_INTERVAL = 300

# RFID認証用鍵の準備
with open("key.txt", "r") as f:
    keys = f.readlines()
keys = [key.strip() for key in keys]
keys = set(keys)
async def authenticate_rfid():
    id_ = RC522.get_rfid()
    if id_ in keys:
        print("RFID authenticated.")
        return True
    else:
        return False
async def detect_human():
    distance = SR04.get_distance()
    if distance < DISTANCE:
        print("Human detected.({:d}cm)".format(distance))
        return distance
    else:
        return False
class State:
    def next_state(self):
        raise NotImplementedError("next_state is abstractmethod")
    def entry_proc(self):
        raise NotImplementedError("entry_proc is abstractmethod")
    def exit_proc(self):
        raise NotImplementedError("exit_proc is abstractmethod")
    def reset(self):
        self.timer = time.time()
class Unlocked(State):
    deg = UNLOCKED_DEG
    def __init__(self):
        self.name = "UNLOCKED"
        self.reset()
    def next_state(self):
        if(LEAD_SWITCH.is_opened()):
            self.reset()
            return "UNLOCKED"
        if (time.time() - self.timer) > UNLOCKED_TIME:
            return "LOCKED"
        else:
            return "UNLOCKED"
    def entry_proc(self):
        print("Unlock!")
        self.reset()
        DS3225.rotate_motor(self.deg)
    def exit_proc(self):
        pass

# Locked状態、exit処理指定フラグ
class Proc(Flag):
    NONE = 0
    LINE = auto()
    GHOME = auto()
class Locked(State):
    deg = LOCKED_DEG
    def __init__(self):
        self.name = "LOCKED"
        self.reset()
        self.exit_proc_flag = Proc.NONE
    def next_state(self):
        if self.should_unlock():
            return "UNLOCKED"
        else:
            return "LOCKED"
    def should_unlock(self):
        loop = asyncio.get_event_loop()
        gather = asyncio.gather(
            authenticate_rfid(),
            detect_human()
        )
        is_rfid_authenticated, is_detected_human = loop.run_until_complete(gather)
        if is_rfid_authenticated:
            if(time.time() - self.timer > NOTIFTY_INTERVAL):
                self.exit_proc_flag |= Proc.LINE
            return True

        if is_detected_human:
            self.exit_proc_flag |= Proc.GHOME
            return True

        return False
    def entry_proc(self):
        print("Lock!")
        self.reset()
        DS3225.rotate_motor(self.deg)
    def exit_proc(self):
        if(Proc.LINE in self.exit_proc_flag):
            asyncio.get_event_loop().run_in_executor(None, LINE.broadcast, "ただいま帰ったでござる。")
            self.exit_proc_flag ^= Proc.LINE
        if(Proc.GHOME in self.exit_proc_flag):
            url = "http://localhost:8091/google-home-notifier?text=http%3A%2F%2F192.168.100.105%2Fkenchi.mp3"
            asyncio.get_event_loop().run_in_executor(None, google_home.notify, url)
            self.exit_proc_flag ^= Proc.GHOME
class Door:
    def __init__(self):
        print('Initializing auto lock system.')
        self.unlocked = Unlocked()
        self.locked = Locked()
        self.states = {self.locked.name: self.locked, self.unlocked.name: self.unlocked}
        self.state = self.unlocked
        self.state.entry_proc()
    def update_state(self):
        # 状態の角度と認識の角度が異なる場合は、一旦解錠
        if self.state.deg != DS3225.get_pos(self.state.deg):
            print('Motor Interrupted!')
            next_state = "UNLOCKED"
        else:
            next_state = self.state.next_state()

        if next_state != self.state.name:
            self.state.exit_proc()
            self.state = self.states[next_state]
            self.state.entry_proc()

if __name__ == "__main__":
    door = Door()
    while True:
        door.update_state()
