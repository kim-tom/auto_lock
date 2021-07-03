import requests
class DS3225:
    @classmethod
    def get_pos(cls, except_value):
        # 例外時は、指定された値を返す。
        deg = except_value
        try:
            deg = int(requests.get("http://localhost:3001/servo/", timeout=(0.5, 0.5)).json()['pos'])
        except requests.exceptions.RequestException as e:
            print("Servo Server:", e.__doc__.strip())
        return deg
    @classmethod
    def rotate_motor(cls, deg):
        try:
            requests.get("http://localhost:3001/servo/" + str(deg), timeout=(0.5, 0.5))
        except requests.exceptions.RequestException as e:
            print("Servo Server:", e.__doc__.strip())
