import requests
class SR04:
    @classmethod
    def get_distance(cls):
        distance = 400
        try:
            json_ = requests.get("http://localhost:3003/", timeout=(0.5, 1.0)).json()
        except requests.exceptions.RequestException as e:
            print("U-Sonic Server:", e.__doc__.strip())
        else:
            distance = int(json_["distance"])
        return distance
