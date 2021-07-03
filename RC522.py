import requests
class RC522:
    @classmethod
    def get_rfid(cls):
        id_ = 0
        try:
            json_ = requests.get("http://localhost:3000/", timeout=(0.5, 0.5)).json()
        except requests.exceptions.RequestException as e:
            print("RFID Server:", e.__doc__.strip())
        else:
            if(type(json_['id']) is list):
                id_ = ','.join(map(str, json_['id']))
        return id_
