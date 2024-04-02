"""
Preprocessing is put in a separate Python module to be able to import it without needing to import the training code
during inference and serving.
"""
import numpy as np


def preprocess(features):
    """Example preprocessing function that can be run as part of training and serving"""
    return np.array(features, dtype="float32") / 2.0 - 1.0
