from pydantic import BaseSettings

from .deployment import Deployment
from .driver import SageMakerDriver
from .orchestrator import Orchestrator


# Use PyDantic BaseSettings to parse configuration
# from environment variables at runtime. For example,
# setting REPLICAS_B to 10 will spawn 10 replicas of
# the B model in this example.
class Settings(BaseSettings):
    replicas_a: int = 1
    replicas_b: int = 2


settings = Settings()


# Deploy a model consisting of two components, A and B, where B
# has twice as many replicas e.g. to handle more load.
# pylint: disable=no-member
handle_a = Deployment.options(name="Model A", num_replicas=settings.replicas_a).bind(model_path="/opt/ml/model/a")
handle_b = Deployment.options(name="Model B", num_replicas=settings.replicas_b).bind(model_path="/opt/ml/model/b")
orchestrator_handle = Orchestrator.bind(handle_a=handle_a, handle_b=handle_b)

handle = SageMakerDriver.options().bind(model_handle=orchestrator_handle)
