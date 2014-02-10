'''
Created on Jul 31, 2012

@author: arenduchintala
'''

import math
import pickle
import numpy
from scipy import stats


def dbgprint(*args):
    return


class GaussianNaiveBayes(object):
    '''
    classdocs
    gaussian naive bayes classifier
    a single training instance tuple:
    (label, [(feature,value), (feature,value), (feature,value)... ])

    a single test instance tuple:

    (0, [(feature,value), (feature,value), (feature,value)... ])
    *zero values can be ignored in test

    data types:
    label preferred  type int
    feature preferred  type int
    value (weight of a feature) preferred type int/float
    '''

    def __init__(self, null_value):
        """
        Constructor
        """
        self.classmodels_count = {}
        self.classmodels = {}
        self.classmodelsMeanAndVariance = {}
        self.featureTokenCount = 0
        self.featureTypeCount = 0
        self.null_value = null_value

    def train(self, training_vecs):

        for item in training_vecs:
            current_class = item[0]
            feature_vector = item[1]
            dbgprint("Current class: ", current_class, "feature_vector: ", feature_vector)

            if current_class in self.classmodels:
                current_class_model = self.classmodels[current_class]
                self.classmodels_count[current_class] += 1
            else:
                current_class_model = {}
                self.classmodels_count[current_class] = 1

            for feature, value in enumerate(feature_vector):
                if float(value) == float(self.null_value):  # TODO
                    continue
                if feature in current_class_model:
                    list_of_values = current_class_model[feature]
                else:
                    list_of_values = []
                list_of_values.append(value)
                current_class_model[feature] = list_of_values

            self.classmodels[current_class] = current_class_model

        for a_class in self.classmodels.keys():
            a_class_model = self.classmodels[a_class]
            a_class_model_mean_and_variance = {}
            for feature in a_class_model.keys():
                # mean = numpy.array(a_class_model[feature]).mean()
                # std = numpy.array(a_class_model[feature]).std()
                classmodelfeatures = map(float, a_class_model[feature])
                mean = numpy.mean(classmodelfeatures)
                std = numpy.std(classmodelfeatures)
                #limit the standard deviation to a minimum of 0.1
                minimum = 1
                std = (std, minimum)[std < minimum]
                a_class_model_mean_and_variance[feature] = (mean, std)
            self.classmodelsMeanAndVariance[a_class] = a_class_model_mean_and_variance

    def classify(self, feature_vec):
        outputs = []
        class_model_output_prob = {}
        for a_class in self.classmodelsMeanAndVariance.keys():
            a_class_output_prob = 0.0
            a_class_model_mean_and_variance = self.classmodelsMeanAndVariance[a_class]
            for feature, value in enumerate(feature_vec):
                #simply ignore a feature if its not seen in training
                if float(value) == float(self.null_value):  # TODO
                    continue
                if feature in a_class_model_mean_and_variance:
                    feature_mean = a_class_model_mean_and_variance[feature][0]
                    feature_std = a_class_model_mean_and_variance[feature][1]
                    dbgprint("value:", float(value), "mean:", feature_mean, "std:", feature_std)
                    dbgprint("pdf:", stats.norm.pdf(float(value), feature_mean, feature_std))
                    prob = max(0.0001, stats.norm.pdf(float(value), feature_mean, feature_std))
                    a_class_output_prob += math.log10(prob)

            #ignoring P(class) prior.. assuming equal priors
            class_model_output_prob[a_class_output_prob] = a_class
        probs = class_model_output_prob.keys()
        probs.sort(reverse=True)
        for prob in probs:
            outputs.append(class_model_output_prob[prob])
        return outputs

    def saveModel(self, filename):
        output_file = open(filename, 'wb')
        pickle.dump((self.classmodels_count, self.classmodelsMeanAndVariance), output_file)
        output_file.flush()
        output_file.close()

    def loadModel(self, filename):
        input_file = open(filename, 'rb')
        items = pickle.load(input_file)
        self.classmodels_count = items[0]
        self.classmodelsMeanAndVariance = items[1]
