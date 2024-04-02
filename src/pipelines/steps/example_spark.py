import os

from sagemaker import Session
from sagemaker.network import NetworkConfig
from sagemaker.processing import ProcessingInput, ProcessingOutput, Processor
from sagemaker.workflow.parameters import ParameterString
from sagemaker.workflow.properties import PropertyFile
from sagemaker.workflow.steps import ProcessingStep
from typer import Option, run

from pipelines.common import get_network_config, get_sagemaker_session
from pipelines.constants import PIPELINES_EXECUTION_ROLE, PROCESSING_IMAGE_URI

# Use module constants to avoid errors due to typos in naming and paths
PROPERTY_OUTPUT_NAME = "properties"
PROPERTY_OUTPUT_SOURCE = "/opt/ml/processing/properties"
PROPERTY_FILE_PATH = "properties.json"
PROPERTY_FILE_NAME = "uris"
OUTPUT_URI_NAME = "output-uri"


class ExampleSparkProcessor(ProcessingStep):
    @property
    def output_uri(self) -> str:
        """Return the S3 URI of processed data."""
        # pylint: disable=no-member
        return self.properties.ProcessingOutputConfig.Outputs[OUTPUT_URI_NAME].S3Output.S3Uri


def run_processor(
    input_uri,
    output_uri,
    properties_uri,
    sagemaker_session,
    network_config,
):
    # Even though SageMaker provides a PySparkProcessor, we are using the more general
    # Processor class here. PySparkProcessor only supports running Scripts by uploading
    # them to S3 first, which makes packaging and deployment fragile. smspark-submit
    # takes care of the proper bootstrapping of a spark cluster on SageMaker instances
    processor = Processor(
        role=PIPELINES_EXECUTION_ROLE,
        image_uri=os.environ.get(
            "PROCESSING_IMAGE_URI",
            PROCESSING_IMAGE_URI,
        ),
        entrypoint=["smspark-submit", "/runtime/scripts/example_spark.py"],
        instance_count=2,
        instance_type="ml.c5.2xlarge",
        base_job_name="example-spark-processor",
        sagemaker_session=sagemaker_session,
        network_config=network_config,
    )

    return processor.run(
        inputs=[
            ProcessingInput(
                input_name="input-uri",
                source=input_uri,
                app_managed=True,
                destination="/opt/ml/processing/dummy",
            )
        ],
        outputs=[
            ProcessingOutput(
                output_name=PROPERTY_OUTPUT_NAME,
                source=PROPERTY_OUTPUT_SOURCE,
                destination=properties_uri,
            ),
            ProcessingOutput(
                output_name=OUTPUT_URI_NAME,
                source="/opt/ml/processing/dummy",
                destination=output_uri,
                app_managed=True,
            ),
        ],
        arguments=[
            "--input-uri",
            input_uri,
            "--output-uri",
            output_uri,
            "--properties-file",
            f"{PROPERTY_OUTPUT_SOURCE}/{PROPERTY_FILE_PATH}",
        ],
    )


def get_step(
    input_uri: ParameterString,
    output_uri: str,
    properties_uri: str,
    sagemaker_session: Session,
    network_config: NetworkConfig,
) -> ExampleSparkProcessor:
    return ExampleSparkProcessor(
        name="example-spark-processing-step",
        step_args=run_processor(
            input_uri,
            output_uri,
            properties_uri,
            sagemaker_session,
            network_config,
        ),
        property_files=[
            PropertyFile(
                name=PROPERTY_FILE_NAME,
                output_name=PROPERTY_OUTPUT_NAME,
                path=PROPERTY_FILE_PATH,
            )
        ],
    )


def main(
    input_uri: str = Option(..., help="S3 URI of input data directory"),
    output_uri: str = Option(..., help="S3 URI of output data directory"),
    properties_uri: str = Option(..., help="S3 URI of output properties file"),
):
    run_processor(
        input_uri,
        output_uri,
        properties_uri,
        sagemaker_session=get_sagemaker_session(return_session=True),
        network_config=get_network_config(),
    )


if __name__ == "__main__":
    run(main)
