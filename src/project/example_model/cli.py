import logging
import os
import pathlib

import pandas as pd
from typer import Option, Typer

from project.example_model.training import Hyperparameters, evaluate_model, train_model

logger = logging.getLogger(__name__)
app = Typer()


@app.command()
def main(
    training_data_dir: pathlib.Path = Option(
        "/opt/ml/input/data/training",
        exists=True,
        help="Local directory for training data.",
    ),
    model_output_dir: pathlib.Path = Option(
        "/opt/ml/model",
        help="Local directory for saved model.",
    ),
    # When using the SageMaker Training Jobs, you can either load the
    # hyperparameters from hyperparameters.json, located in the directory
    # /opt/ml/input/config/, or parse them from the command line directly.
    # When loading hyperparameters from disk, it is recommended to use a Python data
    # structure like the PyDantic Model in this example.
    hyperparameters_path: pathlib.Path = Option("/opt/ml/input/config/hyperparameters.json"),
):
    logging.basicConfig(level="INFO")

    logger.info("Reading training data from %s...", training_data_dir)
    train_data = pd.read_parquet(training_data_dir / "clean.parquet")

    # Load hyperparameters from disk if they exist or use the defaults
    # defined in the model class.
    hyperparameters = (
        Hyperparameters.parse_file(hyperparameters_path) if hyperparameters_path.exists() else Hyperparameters()
    )

    logger.info("Using hyperparameters %s", hyperparameters)

    logger.info("Training model...")
    model = train_model(train_data, hyperparameters)
    evaluate_model(train_data, model, "train")

    model_output_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_output_dir / "model.savedmodel"

    logger.info("Saving model to %s", model_path)
    model.save(model_path)
