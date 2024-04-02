from typing import Optional

from sagemaker.network import NetworkConfig
from sagemaker.session import Session
from sagemaker.workflow.parameters import ParameterString
from sagemaker.workflow.pipeline import (
    ExecutionVariables,
    Pipeline,
    PipelineExperimentConfig,
)
from typer import Option, run

import pipelines.constants
import pipelines.steps.example_processor
import pipelines.steps.example_register
import pipelines.steps.example_spark
import pipelines.steps.example_training
from pipelines.common import (
    get_network_config,
    get_path_prefixer,
    get_sagemaker_session,
    get_user_enumber,
)


def get_pipeline(
    sagemaker_session: Session,
    network_config: NetworkConfig,
) -> Pipeline:
    raw_data_path = ParameterString(name="RawDataPath")
    s3_prefix = ParameterString(
        name="S3Prefix",
        default_value="s3://sagemaker-1985-10-10/my-project",
    )

    # This creates a helper function that all steps can use to construct consistent
    # S3 paths with the same prefixes. In this example, we are using a user provided
    # prefix and attach the execution ID. This will result in unique paths for each
    # execution. Note that this effectively makes step caching impossible, as the paths
    # will change in each execution.
    path_for = get_path_prefixer(s3_prefix, ExecutionVariables.PIPELINE_EXECUTION_ID)

    preprocessing_output_uri = path_for("processed")
    preprocess_step = pipelines.steps.example_processor.get_step(
        raw_data_path=raw_data_path,
        output_uri=preprocessing_output_uri,
        sagemaker_session=sagemaker_session,
        network_config=network_config,
    )

    spark_output_uri = path_for("spark", "output.parquet")
    spark_properties_uri = path_for("spark", "properties")
    spark_step = pipelines.steps.example_spark.get_step(
        input_uri=preprocess_step.processed_data_file,
        output_uri=spark_output_uri,
        properties_uri=spark_properties_uri,
        sagemaker_session=sagemaker_session,
        network_config=network_config,
    )

    model_output_path = path_for("example-model", "model")
    training_step = pipelines.steps.example_training.get_step(
        training_data_uri=preprocess_step.processed_data_prefix,
        output_path=model_output_path,
        sagemaker_session=sagemaker_session,
        network_config=network_config,
    )

    model_step = pipelines.steps.example_register.get_step(
        model_data=training_step.model_artifacts,
        sagemaker_session=sagemaker_session,
    )

    return Pipeline(
        name="ExamplePipeline",
        sagemaker_session=sagemaker_session,
        pipeline_experiment_config=PipelineExperimentConfig(
            experiment_name="ExampleExperiment",
            trial_name=ExecutionVariables.PIPELINE_EXECUTION_ID,
        ),
        parameters=[
            raw_data_path,
            s3_prefix,
        ],
        steps=[
            preprocess_step,
            training_step,
            model_step,
            spark_step,
        ],
    )


def main(
    raw_data_path: Optional[str] = Option(None),
):
    sagemaker_session = get_sagemaker_session()
    network_config = get_network_config()

    pipeline = get_pipeline(sagemaker_session, network_config)

    pipeline.upsert(
        role_arn=pipelines.constants.PIPELINES_EXECUTION_ROLE,
        tags=[{"Key": "E-Number", "Value": get_user_enumber()}] + pipelines.constants.TAGS_PIPELINE,
    )

    if raw_data_path:
        pipeline.start(parameters={"RawDataPath": raw_data_path})


if __name__ == "__main__":
    run(main)
