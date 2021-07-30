import requests
class DS3225:
    server_port = 3001
    session = requests.Session()
    @classmethod
    def get_pos(cls, except_value):
        # 例外時は、指定された値を返す。
        deg = except_value
        try:
            deg = int(cls.session.get(f"http://localhost:{cls.server_port}/servo/", timeout=(0.5, 0.5)).json()['deg'])
        except requests.exceptions.RequestException as e:
            print("Servo Server:", e.__doc__.strip())
        return deg
    @classmethod
    def rotate_motor(cls, deg):
        try:
            cls.session.get(f"http://localhost:{cls.server_port}/servo/{deg}")
        except requests.exceptions.RequestException as e:
            print("Servo Server:", e.__doc__.strip())

if __name__ == '__main__':
    import logging, requests, time
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")
    while True:
        id_ = DS3225.get_pos(1)
        time.sleep(0.1)
