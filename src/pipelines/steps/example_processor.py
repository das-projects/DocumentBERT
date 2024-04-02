import os

from sagemaker.processing import ProcessingInput, ProcessingOutput, Processor
from sagemaker.workflow.functions import Join, JsonGet
from sagemaker.workflow.parameters import ParameterString
from sagemaker.workflow.properties import PropertyFile
from sagemaker.workflow.steps import ProcessingStep
from typer import Option, run

from pipelines.common import get_network_config, get_sagemaker_session
from pipelines.constants import PIPELINES_EXECUTION_ROLE, PROCESSING_IMAGE_URI

PROCESSED_DATA_NAME = "processed"


class ExampleProcessingStep(ProcessingStep):
    """Subclass to add nicer access to step attributes."""

    @property
    def processed_data_file(self) -> str:
        """Return the S3 URI of processed data file."""
        # pylint: disable=no-member
        file_name = JsonGet(
            step_name=self.name,
            property_file="properties",
            json_path="cleanData",
        )

        return Join(
            on="/",
            values=[
                self.processed_data_prefix,
                file_name,
            ],
        )

    @property
    def processed_data_prefix(self):
        """Return the S3 URI of processed data prefix."""
        # pylint: disable=no-member
        return self.properties.ProcessingOutputConfig.Outputs[PROCESSED_DATA_NAME].S3Output.S3Uri


def run_processor(
    raw_data_path,
    output_uri,
    sagemaker_session,
    network_config,
):
    processor = Processor(
        role=PIPELINES_EXECUTION_ROLE,
        # Make the Docker image URI overridable from environment variables
        # for quick iteration on individual steps.
        image_uri=os.environ.get(
            "PROCESSING_IMAGE_URI",
            PROCESSING_IMAGE_URI,
        ),
        sagemaker_session=sagemaker_session,
        network_config=network_config,
        instance_count=1,
        instance_type="ml.c5.2xlarge",
        # Images based on pre-built AWS images might have multiple Python versions
        # in them. Make sure to select the correct one by explicitly referring to
        # the correct binary.
        entrypoint=["/runtime/venv/bin/processing"],
        base_job_name="example-processor",
    )

    return processor.run(
        inputs=[
            ProcessingInput(
                input_name="raw-data",
                source=raw_data_path,
                destination="/opt/ml/processing/raw",
            ),
        ],
        outputs=[
            ProcessingOutput(
                output_name=PROCESSED_DATA_NAME,
                source="/opt/ml/processing/processed",
                destination=output_uri,
            ),
        ],
        arguments=[
            "--raw-data-path",
            "/opt/ml/processing/raw/raw.csv",
            "--output-dir",
            "/opt/ml/processing/processed",
        ],
    )


def get_step(
    raw_data_path: ParameterString,
    output_uri: str,
    sagemaker_session,
    network_config,
) -> ExampleProcessingStep:
    return ExampleProcessingStep(
        name="example-processing-step",
        display_name="Example Processing Step",
        description=(
            "Illustrates the use of ProcessingSteps with custom images and " "and SageMaker inputs and outputs."
        ),
        step_args=run_processor(
            raw_data_path,
            output_uri,
            sagemaker_session,
            network_config,
        ),
        property_files=[
            PropertyFile(
                "properties",
                PROCESSED_DATA_NAME,
                "properties.json",
            ),
        ],
    )


def main(
    raw_data_path: str = Option(..., help="S3 URI of raw data"),
    output_uri: str = Option(..., help="S3 prefix URI of cleaned data"),
):
    """Run the example processor in an individual SageMaker Processing Job."""
    run_processor(
        raw_data_path,
        output_uri,
        sagemaker_session=get_sagemaker_session(return_session=True),
        network_config=get_network_config(),
    )


if __name__ == "__main__":
    run(main)
