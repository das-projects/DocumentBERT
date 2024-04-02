"""
Various functions used in the pipeline and steps
"""
from typing import Union

from sagemaker.network import NetworkConfig
from sagemaker.session import Session
from sagemaker.workflow.functions import Join
from sagemaker.workflow.pipeline_context import PipelineSession

from pipelines.constants import NETWORK_CONFIG

__all__ = [
    "get_sagemaker_session",
    "get_network_config",
    "get_path_prefixer",
    "get_user_enumber",
]


def get_sagemaker_session(return_session=False) -> Union[Session, PipelineSession]:
    """Configure and return a SageMaker session.

    Most likely useful for setting the default bucket. When submitting
    individual jobs, a "normal" Session is required. For Pipeline setup,
    a PipelineSession is required.
    """
    if return_session:
        return Session()

    return PipelineSession()


def get_network_config() -> NetworkConfig:
    """Configure and return a NetworkConfig.

    Running SageMaker Jobs within ERGOs networking setup requires
    setting the correct VPC and Subnet values.
    """
    return NetworkConfig(**NETWORK_CONFIG)


def get_path_prefixer(*prefixes):
    """Returns a callable that joins path fragments with the given prefix."""

    def path_for(*parts):
        """Helper to construct consistent S3 paths from the given prefix."""
        return Join(
            on="/",
            values=[*prefixes, *parts],
        )

    return path_for


def get_user_enumber() -> str:
    """
        Retrieve the callers e-number
    Returns:
        callers e-number as a string
    """
    import boto3

    user_id = boto3.client("sts").get_caller_identity().get("UserId")
    start_index = user_id.index(":") + 1
    end_index = user_id.index("@")
    e_number = user_id[start_index:end_index]
    return e_number
