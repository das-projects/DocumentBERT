from pydantic import BaseSettings

from .deployment import Deployment
from .driver import SageMakerDriver


# Use PyDantic BaseSettings to parse configuration
# from environment variables at runtime. For example,
# to set model_path, set the environment variable
# MODEL_PATH to the desired value.
class Settings(BaseSettings):
    model_name: str = "Model A"
    model_path: str = "/opt/ml/model"


settings = Settings()

# pylint: disable=no-member
model_handle = Deployment.options(name=settings.model_name).bind(model_path=settings.model_path)
handle = SageMakerDriver.bind(model_handle=model_handle)
