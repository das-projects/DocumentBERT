"""
Example training script
"""
import logging
from typing import Tuple

import keras
import keras.layers
import pandas as pd
from pydantic import BaseModel

from project.example_model.preprocessing import preprocess

logger = logging.getLogger(__name__)


class Hyperparameters(BaseModel):
    """
    Defining the Hyperparameters as a PyDantic Model makes loading and validating parameters from JSON files simpler
    and provides editor support when using the parameters in code.
    """

    input_size: int = 3
    output_size: int = 2
    hidden_size: int = 10


def split_features_targets(data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split features from target column"""
    features = data.drop("Target", axis="columns")
    targets = data["Target"]

    return features, targets


def get_model(hyperparameters: Hyperparameters) -> keras.Model:
    """
    Using a function to return a fully compiled model based on hyperparameters makes implementing hyperparameter
    search easier

    Args:
        hyperparameters ():

    Returns:

    """

    inputs = keras.Input(shape=(hyperparameters.input_size,))
    hidden = keras.layers.Dense(hyperparameters.hidden_size, activation="relu")
    outputs = keras.layers.Dense(hyperparameters.output_size, activation="softmax")

    model = keras.Model(inputs, outputs(hidden(inputs)))
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["SparseCategoricalAccuracy"],
    )

    return model


def train_model(
    train_data: pd.DataFrame,
    hyperparameters: Hyperparameters,
) -> keras.Model:
    """Train model"""

    model = get_model(hyperparameters)

    raw_features, targets = split_features_targets(train_data)
    features = preprocess(raw_features)

    model.fit(
        features,
        targets,
        verbose=2,
    )

    return model


def evaluate_model(
    data: pd.DataFrame,
    model: keras.Model,
    channel: str,
) -> dict:
    """Evaluate model"""
    raw_features, targets = split_features_targets(data)
    features = preprocess(raw_features)
    metrics = model.evaluate(
        features,
        targets,
        return_dict=True,
        verbose=2,
    )

    # Logging metrics in a regex-parsable format to extract
    # them in SageMaker training jobs
    for metric, value in metrics.items():
        logger.info("%s:%s=%.4f", channel, metric, value)

    return metrics
