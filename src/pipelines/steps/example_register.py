from sagemaker.workflow.model_step import Model, ModelStep

from pipelines.constants import SERVING_IMAGE_URI


def get_step(model_data, sagemaker_session):
    model = Model(
        image_uri=SERVING_IMAGE_URI,
        model_data=model_data,
        sagemaker_session=sagemaker_session,
    )

    return ModelStep(
        name="example-register-model-step",
        step_args=model.register(
            content_types=["application/json"],
            response_types=["application/json"],
            inference_instances=["ml.c5.2xlarge"],
            transform_instances=["ml.c5.2xlarge"],
            model_package_group_name="example-package-group",
        ),
    )
