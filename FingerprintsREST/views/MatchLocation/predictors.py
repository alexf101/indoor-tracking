from operator import itemgetter
from sklearn import svm
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import RandomForestClassifier
from numpy import nan
import math
from FingerprintsREST.views.MatchLocation.GaussianNB import GaussianNaiveBayes
from wasp import Redpin
from logging import getLogger
log = getLogger(__name__)


def stripMagnets(data):
    return map(lambda r: r[:-3], data)


def stripMagnetsAndNanify(data, null_value):
    datacopy = []
    for row in data:
        datacopyrow = []
        for value in row[:-3]:
            if value == null_value:
                datacopyrow.append(nan)
            else:
                datacopyrow.append(value)
        datacopy.append(datacopyrow)
    return datacopy


class predictor():

    def fit(self, data, classes):
        pass  # remember to save classes as classes_

    def predict(self, vector):
        pass  # returns [classes], in descending order of probability


class redpin(predictor):

    def __init__(self, null_value):
        self.null_value = null_value
        log.debug("Redpin: ncap=-0.3, nnap=-0.15, sim=1, sigpen=15")
        self.model = Redpin(SIGNAL_PENALTY_THRESHOLD = 15, SIGNAL_GRAPH_WEIGHTING = 0.15, SIMILARITY_WEIGHTING = 1, NNAP_WEIGHTING = -0.15, NCAP_WEIGHTING = -0.3)

    def fit(self, data, classes):
        self.classes_ = classes
        data = stripMagnets(data)
        return self.model.train(self.null_value, data, classes)

    def predict(self, vector):
        return self.model.classify(vector)



class wrapped_svm(predictor):
    def __init__(self, null_value):
        self.model = svm.LinearSVC()

    def fit(self, data, classes):
        self.classes_ = classes
        data = stripMagnets(data)
        return self.model.fit(data, classes)

    def predict(self, vector):
        classes = self.classes_
        vector = vector[:-3]
        if len(classes) == 2:  # decision_function has an odd return value if only two classes, so use predict instead
            prediction = self.model.predict(vector)
            other = classes[0] if prediction == classes[1] else classes[1]
            return [prediction, other]
        else:
            result = zip(self.classes_, self.model.decision_function(vector)[0])
            result.sort(key=itemgetter(1))
            return map(itemgetter(0), result)


class wrapped_randomforest(predictor):
    def __init__(self, null_value):
        self.model = RandomForestClassifier()
        self.null_value = null_value

    def fit(self, data, classes):
        self.classes_ = classes
        #data = stripMagnets(data)
        return self.model.fit(data, classes)

    def predict(self, vector):
        classes = self.classes_
        #vector = vector[:-3]
        if len(classes) == 2:  # decision_function has an odd return value if only two classes, so use predict instead
            prediction = self.model.predict(vector)
            other = classes[0] if prediction == classes[1] else classes[1]
            return [prediction, other]
        else:
            result = zip(self.classes_, self.model.predict_proba(vector)[0])
            result.sort(key=itemgetter(1))
            return map(itemgetter(0), result)


class wrapped_gaussianNB(predictor):

    def __init__(self, null_value):
        self.model = GaussianNB()
        self.null_value = null_value

    def fit(self, data, classes):
        self.classes_ = classes
        #data = stripMagnets(data)
        return self.model.fit(data, classes)

    def predict(self, vector):
        classes = self.classes_
        #vector = vector[:-3]
        if len(classes) == 2:  # decision_function has an odd return value if only two classes, so use predict instead
            prediction = self.model.predict(vector)
            other = classes[0] if prediction == classes[1] else classes[1]
            return [prediction, other]
        else:
            result = zip(self.classes_, self.model.predict_proba(vector)[0])
            result.sort(key=itemgetter(1))
            return map(itemgetter(0), result)


class wrapped_custom_gaussianNB(predictor):

    def __init__(self, null_value):
        self.model = GaussianNaiveBayes(null_value)

    def fit(self, data, classes):
        self.classes_ = classes
        data = stripMagnets(data)
        data = zip(classes, data)
        return self.model.train(data)

    def predict(self, vector):
        return self.model.classify(vector)



class gaussian_fit(predictor):

    twopi = 2 * 3.1415926

    def __init__(self, null_value, ignore_column_count=3):
        self.null_value = null_value
        # the last three columns are magnetic field results which we're going to ignore for now
        self.ignore_column_count = ignore_column_count

    class Stats():
        def __init__(self):
            self.avg = None
            self.variance = 0
            self.N = 0
            self.sum = 0
            self.sumsquares = 0

    # alpha defines the maximum possible score attainable in a close match with low average variance
    def fit(self, data, classes, alpha=3, beta=0.2):
        self.classes_ = classes  # the class assignment for each row of data
        self.alpha = alpha  # the penalty for base stations in train but not test gets divided by this
        self.beta = beta  # this score is subtracted for base stations in test but not train

        # the dictionary representing the row index in class_stats for each class pk
        unique_classes = list(set(classes))
        class_count = len(unique_classes)
        self.row_index_to_class = dict(zip(range(class_count), unique_classes))
        self.class_to_row_index = dict((v, k) for k, v in self.row_index_to_class.iteritems())

        # it effectively governs how much we care about a true match versus missing data.
        row_length = class_count
        column_length = len(data[0]) - self.ignore_column_count
        self.class_stats = [[self.Stats()] * column_length] * row_length
        self._setAverages(data)
        self._setDevs(data)

    def _setAverages(self, data):
        for row_index, row in enumerate(data):
            this_class = self.classes_[row_index]
            class_index = self.class_to_row_index[this_class]
            for base_station_index, base_station_level in enumerate(row[:-self.ignore_column_count]):
                # each row has self.null_value for missing data, which conveniently takes the value of MIN - 1
                if base_station_level != self.null_value:
                    self.class_stats[class_index][base_station_index].N += 1
                    self.class_stats[class_index][base_station_index].sum += base_station_level
        for row in self.class_stats:
            for stat in row:
                stat.avg = float(stat.sum) / float(stat.N)

    def _setDevs(self, data):
        for row_index, row in enumerate(data):
            this_class = self.classes_[row_index]
            class_index = self.class_to_row_index[this_class]
            for base_station_index, base_station_level in enumerate(row[:-self.ignore_column_count]):
                # we deliberately do NOT ignore values equal to self.null_value here, as they SHOULD
                # be taken to increase the variance proportionately to how strong the signal usually is.
                # we also deliberately do NOT increment N here, as we only want missing values to increase
                # the variance, never decrease it.
                stat = self.class_stats[class_index][base_station_index]
                if stat.avg is not None:
                    diff = base_station_level - stat.avg
                    stat.sumsquares += (diff * diff)
        for row in self.class_stats:
            for stat in row:
                stat.variance = max(1, float(stat.sumsquares) / float(stat.N))

    def dbg(self, *msg):
        print msg

    def predict(self, test_row):
        # must calculate a score for each class, i.e. row, in the class_stats matrix
        results = []*len(self.class_stats)
        for row_index, train_row in enumerate(self.class_stats):
            class_id = self.row_index_to_class[row_index]
            # the class score is the sum of scores for each predictor (many of which will be zero)
            sumOfScores = 0
            for col_index, stat in enumerate(train_row):
                self.dbg("class", class_id, "column", col_index, "stat", stat)
                test_value = test_row[col_index]
                if stat.avg is not None:
                    likeliness = self.getlikeliness(test_value, stat)
                    if test_value == self.null_value:
                        # we use the 'unlikeliness' here as we always want a mismatch to
                        # reduce the probability of a successful match
                        unlikeliness = 1 - likeliness
                        sumOfScores -= unlikeliness / self.alpha
                    else:
                        # the predictor is present in both train and test - increase the score
                        # by how good the match is
                        sumOfScores += likeliness
                else:
                    # if the predictor is present in neither test nor train do not alter the score
                    if test_value == self.null_value:
                        continue
                    else:
                        # the predictor is present in test, but not in train
                        # we simply have no idea of what the value of this base station ought to be
                        # so just fake it by taking away a small number...
                        sumOfScores -= self.beta
            results.append((class_id, sumOfScores))
        results.sort(key=lambda x: x[1], reverse=True)
        return map(lambda x: x[0], results)

    def getlikeliness(self, value, stat):
        difference = value - stat.avg
        difsquared = difference * difference
        return self.normalpdf(difsquared, stat.variance)

    # can be interpreted as the probability that this variable came from this distribution
    def normalpdf(self, difsquared, variance):
        denom = (self.twopi*variance)**.5
        num = math.exp(-difsquared/(2*variance))
        return num/denom


# should be a function that returns a predictor
#predictor = gaussian_fit
#predictor = wrapped_svm
#predictor = wrapped_randomforest
#predictor = wrapped_custom_gaussianNB
predictor = redpin