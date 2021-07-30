import requests
class SIMPLE_SWITCH:
    @classmethod
    def has_key(cls):
        has_key = False
        try:
            json_ = requests.get("http://localhost:3006/", timeout=(0.5, 0.5)).json()
        except requests.exceptions.RequestException as e:
            print("Simple-Switch Server:", e.__doc__.strip())
        else:
            has_key = json_["has_key"]
        return has_key
