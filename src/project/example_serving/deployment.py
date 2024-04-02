import pathlib

import ray
import ray.serve

from .models import Request, Response


@ray.remote
def preprocessing(request: Request) -> str:
    """Dummy preprocessing function.

    If you have CPU-bound preprocessing that needs to happen
    per request, wrap the preprocessing in a Ray remote function
    to process it in parallel, without blocking the inference
    process. Feel free to import preprocessing code from your
    training pipeline or similar. Make sure the dependencies
    for running your preprocessing are also in your serving
    dependencies.
    """
    return "preprocessed " + request.text


@ray.serve.deployment()
class Deployment:
    """Dummy deployment for illustration purposes only.

    Refer to the ray guide for detailed information.
    https://docs.ray.io/en/latest/serve/getting_started.html"""

    def __init__(
        self,
        model_path: pathlib.Path = pathlib.Path("/opt/ml/model"),
    ):
        """Perform your model loading here.

        If you have code that loads a model from a checkpoint in your
        training or evaluation code, feel free to import the code here.
        Make sure that the dependencies in your loading code are also
        part of the serving dependencies. If necessary, refactor your
        training code to have all loading routines in a separate module
        with minimal dependencies.
        """
        self.model = f"loaded from {model_path}"

    async def __call__(self, request: Request) -> Response:
        """Interface to handle single prediction requests.

        This function mainly hands over to `batched` to perform inference
        on many requests in parallel to take advantage of data parallelism
        in ML frameworks.
        """

        # Perform preprocessing asynchronously
        preprocessed: str = await preprocessing.remote(request)

        # Enqueue a prediction request to be handled in a batch
        prediction: str = await self.batched(preprocessed)  # type: ignore

        # Wrap the prediction in a Response object
        return Response(text=prediction)

    @ray.serve.batch(max_batch_size=32)  # type: ignore
    async def batched(self, requests: list[str]) -> list[str]:
        """Perform batched inference on many requests.

        Here you would implement the logic that takes a batch of examples
        and performs inference on them, e.g. calling your `forward` method
        on a torch module or calling `.predict` on an sklearn estimator.

        Refer to the Ray guide to tune your batching setup.
        https://docs.ray.io/en/latest/serve/advanced-guides/dyn-req-batch.html
        """
        return [request + f" predicted {self.model}" for request in requests]
