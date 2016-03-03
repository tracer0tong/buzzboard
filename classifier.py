import pickle
from io import StringIO

import redis
from sklearn import tree
from sklearn.cross_validation import KFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier

from features import Features

CLASSIFIER_NONE = 0
CLASSIFIER_LEARN = 1
CLASSIFIER_STRICT = 2


class Classifier(object):
    ClassifierPrefix = 'clf'
    clf = None

    def __init__(self, host, db, prefix, event_size, classes_size=2, barrier=0.95):
        self.host = host
        self.db = db
        self.prefix = prefix + self.ClassifierPrefix
        self.redis = redis.StrictRedis(self.host, db=self.db)
        self.barrier = barrier
        self.es = event_size
        self.cs = classes_size
        self.error = 1.0
        self.mse = 0.0
        self.kf_cnt = 5
        self.load_mode()

    def switch_mode(self, mode=CLASSIFIER_LEARN):
        self.mode = mode
        self.save_mode()

    def save_classifier(self, clf):
        self.redis.set(self.prefix, pickle.dumps(clf))

    def save_mode(self):
        self.redis.set(self.prefix + 'mode', pickle.dumps(self.mode))

    def load_classifier(self):
        self.clf = pickle.loads(self.redis.get(self.prefix)) if self.redis.get(self.prefix) else None

    def load_mode(self):
        self.mode = pickle.loads(self.redis.get(self.prefix + 'mode')) if self.redis.get(
            self.prefix + 'mode') else CLASSIFIER_LEARN

    def fit(self, events):
        X = []
        y = []
        for e in events:
            X.append(e['features'])
            y.append(1 if e['passed'] else -1)
        if len(y) > 2:
            n_folds = len(y) if len(y) < self.kf_cnt else self.kf_cnt
            kf = KFold(len(y), n_folds=n_folds, shuffle=True)
            clf = DecisionTreeClassifier(random_state=1, max_depth=6)
            clf.fit(X, y)
            scores = cross_val_score(clf, X, y, scoring='accuracy', cv=kf)
            error_scores = cross_val_score(clf, X, y, scoring='mean_squared_error', cv=kf)
            self.error = scores.mean()
            self.mse = error_scores.mean()
            print('Accuracy={0}'.format(self.error))
            print('MSE={0}'.format(self.mse))
            self.save_classifier(clf)

    def classify(self, event):
        self.load_classifier()
        if self.clf:
            print('Event for classification: {0}'.format(event))
            return self.clf.predict([event])[0]
        else:
            return 0

    def precision(self, barrier=0.95):
        self.barrier = barrier

    def get_dot(self):
        dot_data = StringIO()
        self.load_classifier()
        if self.clf:
            tree.export_graphviz(self.clf, out_file=dot_data, class_names=['Spamer', 'Normal'], feature_names=[f.name() for f in Features], filled=True, rounded=True, special_characters=True)
        return dot_data.getvalue()

    def get_mode(self):
        return self.mode

    def get_feature_weight(self):
        self.load_classifier()
        if self.clf:
            return list(self.clf.feature_importances_)
        else:
            return [0] * self.es

    def ready(self):
        if self.error < self.barrier:
            return False
        else:
            return True

    def clean(self):
        self.redis.delete(self.prefix)
        self.redis.delete(self.prefix + 'mode')
