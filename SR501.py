import requests
class SR501:
    @classmethod
    def sr501_request():
        detect = False
        try:
            json_ = requests.get("http://localhost:3002/", timeout=(0.5, 0.5)).json()
        except requests.exceptions.RequestException as e:
            print("PIR Server:", e.__doc__.strip())
        else:
            detect = json_["detect"]
        return detect
