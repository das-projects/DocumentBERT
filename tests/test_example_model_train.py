import pathlib

import pandas as pd
from typer.testing import CliRunner

from project.example_model.cli import app
from project.example_model.training import Hyperparameters, evaluate_model, train_model


def test_train_evaluate_model():
    hp = Hyperparameters()
    df = pd.DataFrame(data=[(1, 2, 3, 0), (2, 3, 4, 1)], columns=["F1", "F2", "F3", "Target"])

    model = train_model(df, hp)

    metrics = evaluate_model(df, model, "train")

    assert len(metrics) == 2


def test_training_cli(tmp_path: pathlib.Path):
    training_data_dir = pathlib.Path(__file__).parent / "data/"
    model_dir = tmp_path / "model"
    runner = CliRunner()
    invocation = runner.invoke(
        app,
        args=["--training-data-dir", str(training_data_dir), "--model-output-dir", str(model_dir)],
    )

    assert invocation.exit_code == 0
