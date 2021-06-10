import time
import requests
import json
import os
from enum import Flag, auto

UNLOCKED_DEG = 175
LOCKED_DEG = 85
STATE_UNLOCKED = 0
STATE_LOCKED = 1
UNLOCKED_TIME = 10
DISTANCE = 50
NOTIFTY_INTERVAL = 300

key_file = open("key.txt", "r")
keys = key_file.readlines()
key_file.close()

# 処理フラグ
class Proc(Flag):
    NONE = 0
    LINE = auto()
    GHOME = auto()

class State:
    def next_state(self):
        raise NotImplementedError("update_state is abstractmethod")
    @staticmethod
    def judge_id(id):
        for key in keys:
            if key.strip('\n') == id:
                return True
        return False
    @staticmethod
    def get_id():
        id = 0
        try:
            json_ = requests.get("http://localhost:3000/", timeout=(0.5, 0.5)).json()
        except requests.exceptions.RequestException as e:
            print("RFID Server:", e.__doc__.strip())
        else:
            if(type(json_['id']) is list):
                id = ','.join(map(str, json_['id']))
        return id
    @staticmethod
    def sr501_request():
        detect = False
        try:
            json_ = requests.get("http://localhost:3002/", timeout=(0.5, 0.5)).json()
        except requests.exceptions.RequestException as e:
            print("PIR Server:", e.__doc__.strip())
        else:
            detect = json_["detect"]
        return detect
    @staticmethod
    def sr04_request():
        distance = 400
        try:
            json_ = requests.get("http://localhost:3003/", timeout=(0.5, 0.5)).json()
        except requests.exceptions.RequestException as e:
            print("U-Sonic Server:", e.__doc__.strip())
        else:
            distance = int(json_["distance"])
        return distance
    @staticmethod
    def is_opened():
        opened = True
        try:
            json_ = requests.get("http://localhost:3005/", timeout=(0.5, 0.5)).json()
        except requests.exceptions.RequestException as e:
            print("L-Switch Server:", e.__doc__.strip())
        else:
            opened = json_["opened"]
        return opened
    @staticmethod
    def detect_human():
        distance = State.sr04_request()
        if distance < DISTANCE:
            return distance
        else:
            return False
    @staticmethod
    def line_broadcast(message):
        try:
            requests.get("http://localhost:3004/broadcast/" + message, timeout=(0.5, 2.0))
        except requests.exceptions.RequestException as e:
            print("LINE Broadcast Server:", e.__doc__.strip())
        else:
            print("LINE message broadcasted.")
    @staticmethod
    def google_home_notifier():
        try:
            requests.get("http://localhost:8091/google-home-notifier?text=http%3A%2F%2F192.168.100.105%2Fkenchi.mp3", timeout=(0.5, 2.0))
        except requests.exceptions.RequestException as e:
            print("GHN Server:", e.__doc__.strip())
    def reset(self):
        self.timer = time.time()
class Unlocked(State):
    deg = UNLOCKED_DEG
    def __init__(self):
        self.name = "UNLOCKED"
        self.reset()
    def next_state(self):
        if(self.is_opened()):
            self.reset()
        if (time.time() - self.timer) > UNLOCKED_TIME:
            return STATE_LOCKED
        else:
            return STATE_UNLOCKED

class Locked(State):
    post_proc_flag = Proc.NONE
    deg = LOCKED_DEG
    def __init__(self):
        self.name = "LOCKED"
        self.reset()
    def next_state(self):
        if self.decide_unlock():
            return STATE_UNLOCKED
        else:
            return STATE_LOCKED
    def decide_unlock(self):
        id = self.get_id()
        if self.judge_id(id):
            print("RFID authenticated.")
            if(time.time() - self.timer > NOTIFTY_INTERVAL):
                self.post_proc_flag |= Proc.LINE
            return True

        distance = self.detect_human()
        if distance:
            print("Human detected.({:d}cm)".format(distance))
            self.post_proc_flag |= Proc.GHOME
            return True

        return False
    def post_proc(self):
        if(Proc.LINE in self.post_proc_flag):
            self.line_broadcast("ただいま帰ったでござる。")
            self.post_proc_flag ^= Proc.LINE
        if(Proc.GHOME in self.post_proc_flag):
            self.google_home_notifier()
            self.post_proc_flag ^= Proc.GHOME
class Door:
    def __init__(self):
        print('Initializing auto lock system.')
        self.unlocked = Unlocked()
        self.locked = Locked()
        self.state = self.unlocked
        self.unlock()
    def update_state(self):
        # 状態の角度と認識の角度が異なる場合は、一旦解錠
        if self.state.deg != self.get_pos():
            print('Motor Interrupted!')
            next_state = STATE_UNLOCKED
        else:
            next_state = self.state.next_state()
        if next_state == STATE_LOCKED:
            self.lock()
            if self.state == self.unlocked:
                self.locked.reset()
                print('Lock!')
                self.state = self.locked
        elif next_state == STATE_UNLOCKED:
            self.unlock()
            if self.state == self.locked:
                self.unlocked.reset()
                self.locked.post_proc()
                print('Unlock.')
                self.state = self.unlocked
    def get_pos(self):
        deg = self.state.deg
        try:
            deg = int(requests.get("http://localhost:3001/servo/", timeout=(0.5, 0.5)).json()['pos'])
        except requests.exceptions.RequestException as e:
            print("Servo Server:", e.__doc__.strip())
        return deg 
    def rotate_motor(self, deg):
        try:
            requests.get("http://localhost:3001/servo/" + str(deg), timeout=(0.5, 0.5))
        except requests.exceptions.RequestException as e:
            print("Servo Server:", e.__doc__.strip())
    def lock(self):
        self.rotate_motor(self.locked.deg)
    def unlock(self):
        self.rotate_motor(self.unlocked.deg)
