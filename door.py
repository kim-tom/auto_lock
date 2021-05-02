import time
import requests
import json
import os

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

class State:
    def next_state(self):
        raise NotImplementedError("update_state is abstractmethod")
    @classmethod
    def judge_id(self, id):
        for key in keys:
            if key.strip('\n') == id:
                return True
        return False
    @classmethod
    def get_id(self):
        id = 0
        try:
            json_ = requests.get("http://localhost:3000/", timeout=(0.5, 0.5)).json()
        except requests.exceptions.ConnectTimeout:
            """RFIDが認識されなかったら、タイムアウトする"""
        except requests.exceptions.RequestException as e:
            print("RFID Server: ", e.__doc__.strip())
        else:
            if(type(json_['id']) is list):
                id = ','.join(map(str, json_['id']))
        return id
    @classmethod
    def sr501_request(self):
        detect = False
        try:
            json_ = requests.get("http://localhost:3002/", timeout=(0.5, 0.5)).json()
        except requests.exceptions.RequestException as e:
            print("PIR Server: ", e.__doc__.strip())
        else:
            detect = json_["detect"]
        return detect
    @classmethod
    def sr04_request(self):
        distance = 400
        try:
            json_ = requests.get("http://localhost:3003/", timeout=(0.5, 0.5)).json()
        except requests.exceptions.RequestException as e:
            print("U-Sonic Server: ", e.__doc__.strip())
        else:
            distance = float(json_["distance"])
        return distance
    @classmethod
    def is_opened(self):
        opened = True
        try:
            json_ = requests.get("http://localhost:3005/", timeout=(0.5, 0.5)).json()
        except requests.exceptions.RequestException as e:
            print("L-Switch Server: ", e.__doc__.strip())
        else:
            opened = json_["opened"]
        return opened
    @classmethod
    def detect_human(self):
        distance = self.sr04_request()
        if distance < DISTANCE:
            return distance
        else:
            return False
    @classmethod
    def line_broadcast(self, message):
        try:
            requests.get("http://localhost:3004/broadcast/" + message, timeout=(0.5, 0.5)).json()
        except requests.exceptions.RequestException as e:
            print("LINE Broadcast Server: ", e.__doc__.strip())
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
        distance = self.detect_human()
        if self.judge_id(id):
            print("RFID found.")
            if(time.time() - self.timer > NOTIFTY_INTERVAL):
                self.line_broadcast("ただいま帰ったでござる。")
            return True
        elif distance:
            print("Human found.({:d}cm)".format(int(distance)))
            return True
        else:
            return False

class Door:
    def __init__(self):
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
            if self.state == self.unlocked:
                self.locked.reset()
            self.state = self.locked
            self.lock()
        elif next_state == STATE_UNLOCKED:
            if self.state == self.locked:
                self.unlocked.reset()
            self.state = self.unlocked
            self.unlock()
    def get_pos(self):
        try:
            deg = int(requests.get("http://localhost:3001/servo/", timeout=(0.5, 0.5)).json()['pos'])
        except requests.exceptions.RequestException as e:
            print("Servo Server: ", e.__doc__.strip())
        return deg 
    def rotate_motor(self, deg):
        try:
            requests.get("http://localhost:3001/servo/" + str(deg), timeout=(0.5, 0.5)).json()
        except requests.exceptions.RequestException as e:
            print("Servo Server: ", e.__doc__.strip())
    def lock(self):
        self.rotate_motor(LOCKED_DEG)
    def unlock(self):
        self.rotate_motor(UNLOCKED_DEG)
