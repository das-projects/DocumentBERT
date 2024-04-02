"""
Constants used in the pipeline and steps
"""
import os

import dotenv

# Load environment files to enable setting constants
# using os.environ.get
dotenv.load_dotenv("usecase.env")
dotenv.load_dotenv(".env")

USECASE_NAME = os.getenv("USECASE_NAME")
USECASE_REGISTRY = os.getenv("USECASE_REGISTRY")
BUCKET_MODELING = os.getenv("BUCKET_MODELING")
BUCKET_STAGING = os.getenv("BUCKET_STAGING")

PROCESSING_IMAGE_URI = (
    f"{USECASE_REGISTRY}/{USECASE_NAME}/processing-cpu"
    "@sha256:ca4d200c89528de1d216fa3344774cd9ebc13a5419dbe8f2a340bfc812a2a1a3"
)

TRAINING_IMAGE_URI = (
    f"{USECASE_REGISTRY}/{USECASE_NAME}/training"
    f"@sha256:0996a746912a94174d3d15ffe05da36ac670973d2cea6c70b755366e89bc7589"
)

INFERENCE_IMAGE_URI = (
    f"{USECASE_REGISTRY}/{USECASE_NAME}/serving"
    "@sha256:5e2cac052a2ba61ce2d2e7163705b567943726af91c12e41eedb32147f80b520"
)
# Image for the other Endpoints, if their differ at some point


PIPELINES_EXECUTION_ROLE_ARN = f"arn:aws:iam::906507146617:role/gaa_{USECASE_NAME}_mdev_pipeline-exec"
PIPELINES_EXECUTION_ROLE = f"gaa_{USECASE_NAME}_mdev_pipeline-exec"
DE_EXECUTION_ROLE = f"gaa_{USECASE_NAME}_mdev_data-engineer-sg"
DS_EXECUTION_ROLE = f"gaa_{USECASE_NAME}_mdev_data-scientist-sg"


PREFIX = f"prod/{USECASE_NAME}ract"

NETWORK_CONFIG = {
    "subnets": ["subnet-082f0a8e73e7e3adf"],
    "security_group_ids": ["sg-05a5dc03754415eed"],
}
NETWORK_CONFIG_FOR_ENDPOINTS = {
    "Subnets": ["subnet-082f0a8e73e7e3adf"],
    "SecurityGroupIds": ["sg-05a5dc03754415eed"],
}

TAGS_PIPELINE = [{"Key": "usecase", "Value": f"gaa_{USECASE_NAME}_mdev"}]
TAGS_STEP = {
    "engineer": [
        {"Key": "role", "Value": f"gaa_{USECASE_NAME}_mdev_data-engineer"},
    ],
    "scientist": [
        {"Key": "role", "Value": f"gaa_{USECASE_NAME}_mdev_data-scientist"},
    ],
}

