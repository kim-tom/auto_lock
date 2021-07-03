import requests
class LEAD_SWITCH:
    @classmethod
    def is_opened(cls):
        opened = True
        try:
            json_ = requests.get("http://localhost:3005/", timeout=(0.5, 0.5)).json()
        except requests.exceptions.RequestException as e:
            print("Lead-Switch Server:", e.__doc__.strip())
        else:
            opened = json_["opened"]
        return opened
