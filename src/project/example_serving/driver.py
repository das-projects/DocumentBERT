import fastapi
import ray.serve

from .models import Request, Response

api = fastapi.FastAPI()


# Since the driver does not perform any CPU intensive task
# we don't want it to block resources on the node. Otherwise
# Ray will make sure, that every deployment gets at least a
# single core dedicated to itself.
@ray.serve.deployment(
    ray_actor_options={"num_cpus": 0.0},
)
@ray.serve.ingress(api)
class SageMakerDriver:
    """A Ray Serve Deployment implementing the SageMaker Endpoints API.

    This driver deployment only implements the SageMaker HTTP API
    and does not perform any inference itself but rather hands over
    to the model provided in __init__.
    """

    def __init__(self, model_handle):
        self.model_handle = model_handle

    @api.post("/invocations")
    async def invocations(self, request: Request) -> Response:
        # The first await submits the prediction request...
        response_handle = await self.model_handle.remote(request)

        # The second await waits for the prediction to be done.
        return await response_handle

    @api.get("/ping")
    async def ping(self):
        return "ok"


if __name__ == "__main__":
    # When calling this module directly using
    # python -m project.example_serving.driver
    # it will dump the JSON schema of the API
    # to schema.json
    import json
    import pathlib

    pathlib.Path("schema.json").write_text(json.dumps(api.openapi()))
