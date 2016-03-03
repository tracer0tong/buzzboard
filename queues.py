import pickle

import redis

from settings import REDIS_QUEUE, REDIS_PREFIX


class LearningQueue(object):
    LearningQueuePrefix = 'lq'

    def __init__(self, host, db, prefix):
        self.host = host
        self.db = db
        self.prefix = prefix + self.LearningQueuePrefix
        self.redis = redis.StrictRedis(self.host, db=self.db)

    def save_features(self, uuid, features):
        self.redis.hset(self.prefix, uuid, pickle.dumps(features))

    def load_features(self, uuid=None):
        if uuid:
            features = [pickle.loads(self.redis.hget(self.prefix, uuid))]
        else:
            features = [pickle.loads(x) for x in self.redis.hvals(self.prefix)]
        return features

    def count_items(self, uuid=None):
        if uuid:
            pass
        else:
            return self.redis.hlen(self.prefix)

    def clean(self):
        self.redis.delete(self.prefix)


class MessageQueue(object):
    MessageQueuePrefix = 'mq'
    MessageQueueLookdown = 15

    def __init__(self, host, db, prefix):
        self.host = host
        self.db = db
        self.prefix = prefix + self.MessageQueuePrefix
        self.redis = redis.StrictRedis(self.host, db=self.db)

    def save_message(self, uuid, message):
        self.redis.lpush(self.prefix, pickle.dumps((uuid, message)))

    def load_messages(self, uuid=None):
        messages = [pickle.loads(x) for x in self.redis.lrange(self.prefix, 0, self.MessageQueueLookdown)]
        return messages

    def clean(self):
        self.redis.delete(self.prefix)


class CaptchaQueue(object):
    CaptchaQueuePrefix = 'cq'
    RedirectsPrefix = 'r'
    ProvesPrefix = 'p'
    AttemptsRefix = 'a'

    def __init__(self, host, db, prefix):
        self.host = host
        self.db = db
        self.prefix = prefix + self.CaptchaQueuePrefix
        self.redis = redis.StrictRedis(self.host, db=self.db)

    def check_event(self, uuid, redirect_to):
        pipe = self.redis.pipeline()
        pipe.set(self.prefix + self.RedirectsPrefix + uuid, redirect_to)
        pipe.set(self.prefix + self.AttemptsRefix + uuid, 0)
        pipe.set(self.prefix + self.ProvesPrefix + uuid, 0)
        pipe.execute()

    def prove_event(self, uuid):
        pipe = self.redis.pipeline()
        pipe.incr(self.prefix + self.AttemptsRefix + uuid)
        pipe.set(self.prefix + self.ProvesPrefix + uuid, 1)
        pipe.execute()

    def failed_event(self, uuid):
        pipe = self.redis.pipeline()
        pipe.incr(self.prefix + self.AttemptsRefix + uuid)
        pipe.set(self.prefix + self.ProvesPrefix + uuid, 0)
        pipe.execute()

    def delete_check(self, uuid):
        pipe = self.redis.pipeline()
        pipe.delete(self.prefix + self.RedirectsPrefix + uuid)
        pipe.delete(self.prefix + self.AttemptsRefix + uuid)
        pipe.delete(self.prefix + self.ProvesPrefix + uuid)
        pipe.execute()

    def get_redirect(self, uuid):
        return self.redis.get(self.prefix + self.RedirectsPrefix + uuid)

    def get_result(self, uuid):
        if int(self.redis.get(self.prefix + self.ProvesPrefix + uuid)) == 0:
            res = False
        else:
            res = True
        return res, int(self.redis.get(self.prefix + self.AttemptsRefix + uuid))

    def exists(self, uuid):
        return self.redis.exists(self.prefix + self.ProvesPrefix + uuid)

    def clean(self):
        self.redis.delete(self.prefix)


cq = CaptchaQueue(REDIS_QUEUE['host'], REDIS_QUEUE['db'], REDIS_PREFIX)
lq = LearningQueue(REDIS_QUEUE['host'], REDIS_QUEUE['db'], REDIS_PREFIX)
mq = MessageQueue(REDIS_QUEUE['host'], REDIS_QUEUE['db'], REDIS_PREFIX)
