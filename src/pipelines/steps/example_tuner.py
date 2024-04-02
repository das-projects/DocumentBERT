from sagemaker import Session
from sagemaker.network import NetworkConfig
from sagemaker.tuner import HyperparameterTuner, IntegerParameter
from sagemaker.workflow.steps import TuningStep
from typer import Option, run

from pipelines.common import get_network_config, get_sagemaker_session
from pipelines.steps import example_training


def run_tuner(
    training_data_uri: str,
    output_path: str,
    sagemaker_session: Session,
    network_config: NetworkConfig,
):
    estimator, fit_args = example_training.get_estimator_and_fit_args(
        training_data_uri,
        output_path,
        sagemaker_session,
        network_config,
    )

    tuner = HyperparameterTuner(
        base_tuning_job_name="example-tuner",
        # Note that the HyperparameterTuner does not allow to set
        # environment variables for the individual TrainingJobs it
        # runs. Therefore, we can't set SAGEMAKER_PROGRAM at the time
        # of submission but have to set it in the Docker image.
        estimator=estimator,
        objective_metric_name="train_accuracy",
        metric_definitions=estimator.metric_definitions,
        hyperparameter_ranges={
            "hidden-size": IntegerParameter(min_value=3, max_value=20),
        },
        # Run multiple trials. SageMaker re-uses VMs for repeated jobs
        # which makes it efficient to run many quick training jobs, as
        # pulling large training Docker images only has to be done once.
        max_jobs=10,
        max_parallel_jobs=2,
    )

    # We set wait=False as the output of the tuner when running
    # it individually is not helpful. Go to the AWS console to
    # inspect the process of individual training jobs.
    return tuner.fit(**fit_args, wait=False)


def get_step(
    training_data_uri: str,
    output_path: str,
    sagemaker_session: Session,
    network_config: NetworkConfig,
):
    return TuningStep(
        name="example-tuner",
        step_args=run_tuner(
            training_data_uri,
            output_path,
            sagemaker_session,
            network_config,
        ),
    )


def main(
    training_data_uri: str = Option(..., help="S3 prefix URI of training data"),
    output_path: str = Option(..., help="S3 prefix URI of trained model"),
):
    """Run the tuning step on its own."""

    run_tuner(
        training_data_uri,
        output_path,
        sagemaker_session=get_sagemaker_session(return_session=True),
        network_config=get_network_config(),
    )


if __name__ == "__main__":
    run(main)
