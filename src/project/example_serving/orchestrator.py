import ray.serve

from .models import Request, Response


# Since the orchestrator does not perform any CPU intensive task
# we don't want it to block resources on the node. Otherwise
# Ray will make sure, that every deployment gets at least a
# single core dedicated to itself.
@ray.serve.deployment(ray_actor_options={"num_cpus": 0.0})
class Orchestrator:
    """Example orchestrator deployment that handles two models."""

    def __init__(self, handle_a, handle_b):
        self.handle_a = handle_a
        self.handle_b = handle_b

    async def __call__(self, request: Request) -> Response:
        response_handle_a = await self.handle_a.remote(request)
        response_handle_b = await self.handle_b.remote(request)

        response_a = await response_handle_a
        response_b = await response_handle_b

        return Response(text=", ".join((response_a.text, response_b.text)))
