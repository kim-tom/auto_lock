import time
import requests
import json
import os

UNLOCKED_DEG = 175
LOCKED_DEG = 85
STATE_UNLOCKED = 0
STATE_LOCKED = 1
UNLOCKED_TIME = 20
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
        except requests.exceptions.ReadTimeout:
            print("RFID Server ReadTimeout")
        except requests.exceptions.ConnectTimeout:
            print("RFID Server ConnectTimeout")
        else:
            if(type(json_['id']) is list):
                id = ','.join(map(str, json_['id']))
        return id
    @classmethod
    def sr501_request(self):
        detect = False
        try:
            json_ = requests.get("http://localhost:3002/", timeout=(0.5, 0.5)).json()
        except requests.exceptions.ReadTimeout:
            print("PIR Server ReadTimeout")
        except requests.exceptions.ConnectTimeout:
            print("PIR Server ConnectTimeout")
        else:
            detect = json_["detect"]
        return detect
    @classmethod
    def sr04_request(self):
        distance = 400
        try:
            json_ = requests.get("http://localhost:3003/", timeout=(0.5, 0.5)).json()
        except requests.exceptions.ReadTimeout:
            print("Ditance Server ReadTimeout")
        except requests.exceptions.ConnectTimeout:
            print("Distance Server ConnectTimeout")
        else:
            distance = float(json_["distance"])
        return distance
    @classmethod
    def is_opened(self):
        opened = True
        try:
            json_ = requests.get("http://localhost:3005/", timeout=(0.5, 0.5)).json()
        except requests.exceptions.ReadTimeout:
            print("Ditance Server ReadTimeout")
        except requests.exceptions.ConnectTimeout:
            print("Distance Server ConnectTimeout")
        else:
            opened = json_["opened"]
        return opened
    @classmethod
    def detect_human(self):
        if self.sr04_request() < 30:
            return True
        else:
            return False
    @classmethod
    def line_broadcast(self, message):
        try:
            requests.get("http://localhost:3004/broadcast/" + message, timeout=(0.5, 0.5)).json()
        except requests.exceptions.ReadTimeout:
            print("LINE Broadcast Server ReadTimeout")
        except requests.exceptions.ConnectTimeout:
            print("LINE Broadcast Server ConnectTimeout")
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
        if self.judge_id(id):
            print("RFID found.")
            if(time.time() - self.timer > NOTIFTY_INTERVAL):
                self.line_broadcast("帰宅")
            return True
        elif self.detect_human():
            print("Human found.")
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
                self.state.reset()
            self.state = self.locked
            self.lock()
        elif next_state == STATE_UNLOCKED:
            if self.state == self.locked:
                self.state.reset()
            self.state = self.unlocked
            self.unlock()
    def get_pos(self):
        try:
            deg = int(requests.get("http://localhost:3001/servo/", timeout=(0.5, 0.5)).json()['pos'])
        except :
            print('Exception: get_pos()')
            deg = self.state.deg
        return deg 
    def rotate_motor(self, deg):
        try:
            requests.get("http://localhost:3001/servo/" + str(deg), timeout=(0.5, 0.5)).json()
        except requests.exceptions.ReadTimeout:
            print("Servo Server ReadTimeout")
        except requests.exceptions.ConnectTimeout:
            print("Servo Server ConnectTimeout")
    def lock(self):
        self.rotate_motor(LOCKED_DEG)
    def unlock(self):
        self.rotate_motor(UNLOCKED_DEG)
