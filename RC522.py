import requests
class RC522:
    server_port = 3000
    session = requests.Session()
    @classmethod
    def get_rfid(cls):
        id_ = 0
        try:
            res = cls.session.get(f"http://localhost:{cls.server_port}/", timeout=(0.5, 0.5))
            json_ = res.json()
        except requests.exceptions.RequestException as e:
            print("RFID Server:", e.__doc__.strip())
        else:
            if(type(json_['id']) is list):
                id_ = ','.join(map(str, json_['id']))
        return id_
if __name__ == '__main__':
    import logging, requests, timeit
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")
    for i in range(100):
        id_ = RC522.get_rfid()
        # print(id_)
