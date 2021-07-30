import requests
class SIMPLE_SWITCH:
    session = requests.Session()
    @classmethod
    def has_key(cls):
        has_key = False
        try:
            json_ = cls.session.get("http://localhost:3006/26/", timeout=(0.5, 0.5)).json()
        except requests.exceptions.RequestException as e:
            print("Simple-Switch Server:", e.__doc__.strip())
        else:
            has_key = json_["26"]
        return has_key
    @classmethod
    def is_closed(cls):
        closed = False
        try:
            json_ = cls.session.get("http://localhost:3006/2", timeout=(0.5, 0.5)).json()
        except requests.exceptions.RequestException as e:
            print("Lead-Switch Server:", e.__doc__.strip())
        else:
            closed = json_["2"]
        return closed
