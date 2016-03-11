import sys, getopt
import random
import string
from time import sleep

import requests

SPAM_CNT = 100
SPAM_SLEEP = 5
SPAM_HOST = 'http://127.0.0.1:5000/'
SPAM_MESSAGE = 'I\'m evil spam! '
SPAM_MODE = 0


def generate_string(n=10):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))


def send_spam(mode=0):
    for i in range(0, SPAM_CNT):
        if mode == 0:
            r = requests.post(SPAM_HOST, data={'message': SPAM_MESSAGE})
        elif mode == 1:
            r = requests.post(SPAM_HOST,
                              data={'message': SPAM_MESSAGE*2},
                              headers={'User-Agent': generate_string(200)})
        elif mode == 2:
            headers={'User-Agent': generate_string(200)}
            for hn in range(0, 25):
                headers[generate_string(10)] = generate_string(25)
            r = requests.post(SPAM_HOST,
                              data={'message': SPAM_MESSAGE*3},
                              headers=headers)
        print('Got {0} code'.format(r.status_code))
        sleep(SPAM_SLEEP)

if __name__ == '__main__':
    send_spam(mode=int(sys.argv[1]))
