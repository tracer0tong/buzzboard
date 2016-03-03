from recaptcha import submit, displayhtml
from settings import CAPTCHA_PRIVKEY, CAPTCHA_PUBKEY


class Captcha(object):
    def __init__(self, public_key, server_key):
        self.public_key = public_key
        self.server_key = server_key

    def check(self, challenge, response, ip):
        res = submit(challenge, response, self.server_key, ip)
        return res.is_valid

    def generate(self):
        return displayhtml(self.public_key)


cap = Captcha(CAPTCHA_PUBKEY, CAPTCHA_PRIVKEY)
