# Example script showing how to deploy a registered SageMaker model
# in an SageMaker Endpoint to perform model testing. The script
# expects the model package ARN, which can be found in the SageMaker
# Model registry.
from typing import List, Optional

import sagemaker
from typer import Option, Typer

app = Typer()

ENDPOINT_NAME = "my-example-endpoint"


def get_session():
    return sagemaker.Session()


@app.command()
def register_model(
    model_package_group: str = Option(...),
    image_uri: str = Option(...),
    model_data_uri: str = Option(...),
    approve: bool = Option(
        False,
        help="Should the model be automatically approved? Only approved models can be deployed.",
    ),
    env: Optional[List[str]] = Option(None),
):
    model = sagemaker.Model(
        image_uri=image_uri,
        model_data=model_data_uri,
        sagemaker_session=get_session(),
        env=dict(e.split("=", maxsplit=1) for e in env),
    )

    model_package = model.register(
        content_types=["application/json"],
        response_types=["application/json"],
        model_package_group_name=model_package_group,
        approval_status=("Approved" if approve else "PendingManualApproval"),
    )

    print(model_package.model_package_arn)


@app.command()
def deploy_model(
    model_package_arn: str,
    role: str = Option(..., envvar=["SAGEMAKER_ROLE"]),
    instance_type: str = "ml.c5.2xlarge",
):
    model_package = sagemaker.ModelPackage(
        role=role,
        model_package_arn=model_package_arn,
    )
    model_package.deploy(
        initial_instance_count=1,
        instance_type=instance_type,
        endpoint_name=ENDPOINT_NAME,
    )
    print(model_package.endpoint_name)


@app.command()
def delete_endpoint():
    endpoint = sagemaker.Predictor(
        endpoint_name=ENDPOINT_NAME,
    )
    endpoint.delete_endpoint()


if __name__ == "__main__":
    app()
