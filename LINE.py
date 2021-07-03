import requests
class LINE:
    @classmethod
    def broadcast(cls, message):
        try:
            requests.get("http://localhost:3004/broadcast/" + message, timeout=(0.5, 2.0))
        except requests.exceptions.RequestException as e:
            print("LINE Broadcast Server:", e.__doc__.strip())
        else:
            print("LINE message broadcasted.")
