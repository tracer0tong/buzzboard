import random
import uuid
from collections import OrderedDict

from flask import Flask, render_template, request, redirect, abort

from captcha import cap
from classifier import Classifier, CLASSIFIER_LEARN, CLASSIFIER_STRICT
from features import Features, count_features
from queues import cq, lq, mq
from settings import CAPTCHA_PROBABILITY, REDIS_QUEUE, REDIS_PREFIX

app = Flask(__name__)
classifier = Classifier(REDIS_QUEUE['host'], REDIS_QUEUE['db'], REDIS_PREFIX, len(Features))


def get_uuid():
    return str(uuid.uuid4())


@app.route('/clean', methods=['GET'])
def clear():
    cq.clean()
    lq.clean()
    mq.clean()
    classifier.clean()
    return '', 200


@app.route('/strict', methods=['GET'])
def strict():
    if classifier.get_mode() == CLASSIFIER_STRICT:
        classifier.switch_mode(CLASSIFIER_LEARN)
    else:
        if classifier.ready():
            print('Strict mode on!')
            classifier.switch_mode(CLASSIFIER_STRICT)
    return '', 200


@app.route('/', methods=['GET', 'POST'])
def messages():
    mode = classifier.get_mode()
    if mode == CLASSIFIER_LEARN:
        classifier.fit(lq.load_features())
    features = {'passed': False, 'features': count_features(request)}
    score = classifier.classify(features['features'])
    print("Score: {0}".format(score))
    if (mode == CLASSIFIER_STRICT) and (score == -1):
        abort(400)
    request_uuid = get_uuid()
    message = request.form.get('message', None)
    if message:
        mq.save_message(request_uuid, message)
        if (mode == CLASSIFIER_LEARN) and (random.random() < CAPTCHA_PROBABILITY):
            lq.save_features(request_uuid, features)
            return redirect('/captcha?uuid={0}'.format(request_uuid))
    return render_template('messages.html', messages=mq.load_messages())


@app.route('/captcha', methods=['GET', 'POST'])
def showcaptcha():
    if request.method == 'POST':
        uuid = request.form.get('uuid', '')
        challenge = request.form.get('recaptcha_challenge_field')
        response = request.form.get('recaptcha_response_field')
        x_real_ip = request.headers.get("X-Real-IP")
        remote_ip = request.remote_addr if not x_real_ip else x_real_ip
        features = lq.load_features(uuid)[0]
        if cap.check(challenge, response, remote_ip):
            print('Passed!')
            features['passed'] = True
        else:
            print('Failed!')
            features['passed'] = False
        lq.save_features(uuid, features)
        return redirect('/')
    else:
        return render_template('captcha.html', captcha=cap.generate(), uuid=request.args.get('uuid', None))


@app.route('/ml', methods=['GET', 'POST'])
def ml():
    dot = classifier.get_dot().replace('\n', '')
    fw = OrderedDict(zip([f.name() for f in Features], classifier.get_feature_weight()))
    return render_template('ml.html', acc=classifier.error, mse=classifier.mse, train=lq.load_features(uuid=None),
                           mode=classifier.get_mode(), fw=fw, dot=dot)


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
