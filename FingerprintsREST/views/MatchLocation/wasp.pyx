import cython
import operator
from libcpp cimport bool
from libc.math cimport tanh
cimport cpython.array as array
cimport numpy as np
import numpy as np

# returns a list of classes, ordered by weighted modal score
# assumes input is sorted by score, and is a list of tuples of (class, score)
cdef list weighted_mode_sort(list score_tups):
    cdef:
        dict modal_scores
        int clas
        int i, length, oldValue

    length = len(score_tups)
    modal_scores = {}
    for i in range(length):
        clas = score_tups[i][0]
        if clas in modal_scores:
            oldValue = modal_scores[clas]
        else:
            oldValue = 0
        oldValue += (length - i) ** 2 # always positive
        modal_scores[clas] = oldValue

    return list(zip(*sorted(modal_scores.iteritems(), key=operator.itemgetter(1), reverse=True))[0])

cdef class Redpin:
    '''
    __init__ sets algorithm parameters (defaults should be good).

    "Training" just saves the data - this is kNN, so no actual training is needed. However, it does convert the data to c floats (not implemented yet).

    "Testing" classifies as follows:

    # Maximum similarity between unknown point 'x' and known points 'k'
    C(x) = max(Score(k, x))
    Score(k, x) = alpha * NCAP(k, x) - beta * NNAP(k, x) + gamma * similarity(k, x)


    for k in points:


    '''
    cdef:
        # the maximal value smaller than any observd signal for the data set, representing NULL
        int null_value

        # the difference in score that we consider too far for comfort,
        # i.e. reading's that differ by more than this amount should actually penalise the score.
        int SIGNAL_PENALTY_THRESHOLD

        float SIGNAL_GRAPH_WEIGHTING
        float SIMILARITY_WEIGHTING
        float NNAP_WEIGHTING
        float NCAP_WEIGHTING
        np.ndarray data
        np.ndarray classes

    def __reduce__(self):
        state = (self.null_value, self.data, self.classes)
        return (
            Redpin,
            (self.SIGNAL_PENALTY_THRESHOLD, self.SIGNAL_GRAPH_WEIGHTING, self.SIMILARITY_WEIGHTING, self.NNAP_WEIGHTING, self.NCAP_WEIGHTING),
            state,
        )

    def __setstate__(self, state):
        self.null_value, self.data, self.classes = state

    def __init__(self, SIGNAL_PENALTY_THRESHOLD = 15, SIGNAL_GRAPH_WEIGHTING = 0.15, SIMILARITY_WEIGHTING = 1, NNAP_WEIGHTING = -0.5, NCAP_WEIGHTING = -1):
        self.SIGNAL_PENALTY_THRESHOLD = SIGNAL_PENALTY_THRESHOLD
        self.SIGNAL_GRAPH_WEIGHTING = SIGNAL_GRAPH_WEIGHTING
        self.SIMILARITY_WEIGHTING = SIMILARITY_WEIGHTING
        self.NNAP_WEIGHTING = NNAP_WEIGHTING
        self.NCAP_WEIGHTING = NCAP_WEIGHTING

    def train(self, int null_value, data, classes):
        assert len(data) == len(classes)
        if type(data) != np.ndarray:
            data = np.array(data, dtype='f')
        if type(classes) != np.ndarray:
            classes = np.array(classes, dtype='i')
        self.null_value = null_value
        self.data = data
        self.classes = classes

    def classify(self, x, int neighbour_count = 35):
        # x is a feature vector for the unknown point

        cdef:
            int i, j, NCAP, NNAP, class_of_K, rowlen
            int k_exists, x_exists, rep_count
            list scores
            float similarity, score, k_value, x_value
            tuple score_tup
            float[:, :] dataview
            int[:] classview
            float[:] testdataview

        if type(x) != np.ndarray:
            x = np.array(x, 'f')

        scores = []
        rowlen = self.data.shape[1]
        dataview = self.data
        classview = self.classes
        testdataview = x

        if self.data is None:
            raise Exception("Train has not been called on this classifier: self.data is None")

        for i in range(len(self.data)):
            # print "class is", self.classes[i], "type is", type(self.classes[i])
            class_of_K = classview[i]

            # initialise score variables
            similarity = 0
            NCAP = 0
            NNAP = 0

            for j in range(rowlen): # row length
                k_value = dataview[i, j]
                x_value = testdataview[j]

                k_exists = k_value != self.null_value
                x_exists = x_value != self.null_value

                if x_exists != k_exists:  # if the value is in one case but not the other, i.e. mismatch exists.
                    NNAP += 1
                elif x_exists and k_exists:
                    NCAP += 1
                    similarity += self.similarityScore(x_value, k_value)
                else:
                    continue  # neither access point
            score = self.calcScore(similarity, NNAP, NCAP)
            score_tup = class_of_K, score
            scores.append(score_tup)
#		return scores[0]

        # get the average class of the top n hits
        # return classes in order of score
        # return self.stripDupsFromOrderedList(scores)
        # return classes in order of weighted_mode
        return self.finalise(scores, neighbour_count)

    cdef list finalise(self, list scores, int neighbour_count):
        # scores is a list of class_value tuples
        scores.sort(key=operator.itemgetter(1), reverse=True)
        return weighted_mode_sort(scores[:neighbour_count])

    cdef float calcScore(self, float similarity, float NNAP, float NCAP):
        return similarity * self.SIMILARITY_WEIGHTING + NNAP * self.NNAP_WEIGHTING + NCAP * self.NCAP_WEIGHTING

    cdef list stripDupsFromOrderedList(self, list scores):
        cdef:
            int i, prev, current
            list retval

        retval = []
        prev = -1
        for i in range(len(scores)):
            current = scores[i][0]
            if current != prev:
                retval.append(current)
            prev = current
        return retval

    cdef float similarityScore(self, float x_value, float k_value):
        cdef float absolute_error

        absolute_error = x_value - k_value
        if absolute_error == 0:
            return 1  # avoids zero-division error
        elif absolute_error > 0:
            absolute_error *= -1

        return tanh((self.SIGNAL_PENALTY_THRESHOLD + absolute_error) * self.SIGNAL_GRAPH_WEIGHTING)

    # I'm using my own heuristic similarity score (defined above), but this port of redpin's algorithm is included for comparison.
    cdef float redpinSimilarityScore(self, float x_value, float k_value):

        cdef float absolute_error, relative_error, accuracy, relative_error_to_threshold, accuracy_to_threshold, similarity
        # calculate reciprocal error with regards to the value
        absolute_error = x_value - k_value
        if absolute_error == 0:
            return 1  # avoids zero-division error
        elif absolute_error > 0:
            absolute_error *= -1

        relative_error = absolute_error / k_value

        accuracy = 1 / relative_error  # >> 1 for small errors, > 1 for large errors
        #print "Reciprocal error", accuracy, "Relative error", relative_error

        # calculate reciprocal error with regards to the threshold
        relative_error_to_threshold = self.SIGNAL_PENALTY_THRESHOLD / k_value
        accuracy_to_threshold = -1 / relative_error_to_threshold

        print "accuracy", accuracy, "threshold", accuracy_to_threshold, "difference", accuracy - accuracy_to_threshold

        # calculate similarity score16.500000
        similarity = (accuracy - accuracy_to_threshold) * self.SIGNAL_GRAPH_WEIGHTING


        # restrict resulting score to range between [-1, 1] using cut-off
        if similarity > 1:
            similarity = 1
        elif similarity < -1:
            similarity = -1

        return similarity

cdef class Wasp(Redpin):

    #cdef inline float calcScore(self, float similarity, float NNAP, float NCAP):  # need to pass L (class) and AP id (column)
        # NCAP * PMI(L, AP) + NNAP * PMI(L, AP) + sim
    #	return similarity * self.SIMILARITY_WEIGHTING + NNAP * self.NNAP_WEIGHTING + NCAP * self.NCAP_WEIGHTING

    cdef float PMI(self, int location_id, int access_point_id):
        # lookup in table generated during training
        return 1

