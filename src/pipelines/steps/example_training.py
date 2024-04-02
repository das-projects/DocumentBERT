import os

from sagemaker import Session
from sagemaker.estimator import Estimator
from sagemaker.network import NetworkConfig
from sagemaker.workflow.steps import TrainingInput, TrainingStep
from typer import Option, run

from pipelines.common import get_network_config, get_sagemaker_session
from pipelines.constants import PIPELINES_EXECUTION_ROLE, TRAINING_IMAGE_URI


class ExampleTrainingStep(TrainingStep):
    @property
    def model_artifacts(self):
        # pylint: disable=no-member
        return self.properties.ModelArtifacts.S3ModelArtifacts


def get_estimator_and_fit_args(
    training_data_uri: str,
    output_path: str,
    sagemaker_session: Session,
    network_config: NetworkConfig,
):
    """Sets up an Estimator and the arguments required to run fit.

    We return the arguments separately to be able to re-use the Estimator
    as part of a HyperparameterTuner Job. See `example_tuner.py` for more
    info.
    """

    estimator = Estimator(
        image_uri=os.environ.get("TRAINING_IMAGE_URI", TRAINING_IMAGE_URI),
        role=PIPELINES_EXECUTION_ROLE,
        container_entry_point=["training"],
        instance_count=1,
        instance_type="ml.c5.2xlarge",
        base_job_name="example-estimator",
        output_path=output_path,
        # Your estimator needs to emit log statements matching the below
        # regex patterns for metrics to be logged.
        metric_definitions=[
            {
                "Name": "train_loss",
                "Regex": "train:loss=(.+)",
            },
            {
                "Name": "train_accuracy",
                "Regex": "train:sparse_categorical_accuracy=(.+)",
            },
        ],
        hyperparameters={
            "input-size": 3,
            "output-size": 2,
        },
        # Use the argument below to have a separate path for model checkpoints.
        # checkpoint_s3_uri=path_for("example-model", "checkpoints"),
        # Use the arguments below to include pre-trained models in your estimator
        # The model files at the uri will create a new channel named "model"
        # model_uri=path_for("example-model", "pre-trained"),
        sagemaker_session=sagemaker_session,
        network_config=network_config,
        # A profiler can be enabled to generate diagnostics to identify performance
        # bottlenecks during training
        # https://sagemaker-examples.readthedocs.io/en/latest/sagemaker-debugger/debugger_interactive_analysis_profiling/interactive_analysis_profiling_data.html
        disable_profiler=True,
    )

    fit_args = {
        "inputs": {
            "training": TrainingInput(s3_data=training_data_uri),
        }
    }

    return estimator, fit_args


def get_step(
    training_data_uri: str,
    output_path: str,
    sagemaker_session: Session,
    network_config: NetworkConfig,
) -> ExampleTrainingStep:
    estimator, fit_args = get_estimator_and_fit_args(
        training_data_uri,
        output_path,
        sagemaker_session,
        network_config,
    )

    return ExampleTrainingStep(
        name="example-training-step",
        display_name="Train Model",
        step_args=estimator.fit(**fit_args),
    )


def main(
    training_data_uri: str = Option(..., help="S3 prefix URI of training data"),
    output_path: str = Option(..., help="S3 prefix URI of trained model"),
):
    """Run the training step on its own."""

    estimator, fit_args = get_estimator_and_fit_args(
        training_data_uri,
        output_path,
        sagemaker_session=get_sagemaker_session(return_session=True),
        network_config=get_network_config(),
    )

    estimator.fit(**fit_args)


if __name__ == "__main__":
    run(main)
