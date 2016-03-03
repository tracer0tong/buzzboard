from settings import METHODS


class Feature(object):
    def __init__(self, l):
        self.l = l

    def count_factor(self, request):
        return self.l(request)

    def name(self):
        return self.l.__name__


def MethodFeature(request):
    return METHODS.index(request.method)


def UriLengthFeature(request):
    return len(request.url)


def ParamCountFeature(request):
    return len(request.args)


def HeadersCount(request):
    return len(request.headers)


def UALengthFeature(request):
    return len(request.headers.get('User-Agent', ''))


Features = [Feature(MethodFeature),
            Feature(UriLengthFeature),
            Feature(ParamCountFeature),
            Feature(HeadersCount),
            Feature(UALengthFeature)]

FeaturesCount = len(Features)


def count_features(request):
    res = []
    for f in Features:
        res.append(f.count_factor(request))
    return res
