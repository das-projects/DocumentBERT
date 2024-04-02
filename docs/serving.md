# Serving

All trained models are usually hosted in SageMaker Endpoints.
To work with SageMaker Endpoints, the models need to wrapped in an HTTP server adhering to the SageMaker Endpoints protocol.
We use the [Ray Serving framework](https://docs.ray.io/en/latest/serve/getting_started.html) to implement this model server.

To make communication more consistent when it comes to serving, we have agreed to use the terms **endpoint**, **model**, and **component** with the following meaning.
An **endpoint** hosts one or more **models** in separate containers.
Each **model** can consist of one or more **components**.
A **component** is a trained artifact that you would store with your training framework of choice.
There are cases where multiple **components** work together to build a single **model**, e.g. a text classifier component that is followed by an extraction component.

*It is up to the use case to decide how to design the separation of models and orchestration of endpoints*.
This decision should be made and reviewed at the beginning of the technical implementation of the project and communicated with all parties involved.

## Code Walkthrough

In the following, we explain the use of the code examples that can be found at `src/project/example_serving` in this repository.

### `deployment.py`

To serve any model with ray, you need to implement a deployment wrapping model loading, configuring, and inference in a deployment class.
The `__init__` method should accept a path to where the model can be loaded from that should default to `/opt/ml/model`, as this will be the path that SageMaker Endpoints download and extract your `model.tar.gz` file to when hosting a model.
By providing a path, you can override it to a path on your filesystem when performing local testing or writing automated tests.
You need to implement a method that will perform the inference for a single payload.
In this example, we also show how you can make use of the `@ray.remote` decorator and `await` syntax to perform preprocessing in parallel.
We also show how you can make use of automatic request batching to perform inference on many examples in parallel.
This often times leads to better throughput at the cost of individual request latency.
Inference on GPUs can especially benefit from batching.
The decision about the batching parameters or if to perform batching at all depend on the use case and need to be tuned to the latency requirements of the use case and the hardware inference is running on.
Refer to the comments in the code for more details and references.

### `driver.py` and `single.py`

To expose the defined deployment as a HTTP server conforming to the SageMaker endpoints protocol, we wrap it in a so-called driver deployment, defined in `driver.py`.
This deployment uses Ray's FastAPI integration to define the required endpoints and forwards any request to the actual deployment performing the inference.
Its usage is shown in `single.py`, where we import both the defined deployment and driver and use the `.bind` syntax to create the inference graph.
Most use-cases should be able to use this driver deployment without change and only need to adapt the input and output models defined in `models.py`.
If your use case produces multiple models with different request and response payloads, you need to create a separate driver for each of these models and create corresponding request and response models, similar to what is defined in `models.py`.
This script also shows how to use PyDantic `BaseSettings` to parse configuration from environment variables.
It is recommended to keep the number of settings to a minimum and use environment variables to set them, as they can be easily overridden in SageMaker Endpoints.
The resulting `handle` object can be run with Ray serve by executing
`serve run project.example_serving.single:handle` in your local development environment.

### `orchestrator.py` and `multi.py`

In the case where multiple components work together to perform the inference for a single model, you can use Ray serve to perform the orchestration between components.
This pattern in shown in `multi.py`, where we use the deployment defined in `orchestrator.py` to coordinate between multiple instances of the deployment defined in `deployment.py`.
Here we implement the pattern of simultaneous inference of both instances, but you can implement arbitrary logic to perform loops or dependent inference.
`multi.py` also uses the driver deployment defined above to expose the combined model behind a SageMaker-compatible HTTP API.

## Packaging as a Docker Image

To host the model in a SageMaker endpoint, the Ray server needs to be packaged in a Docker image together with its runtime dependencies.
Refer to [the Docker guide](docker.md) for details on how to build and push Docker images.
Refer to the `Dockerfile` and the comments below the line `FROM runtime-base as serving` for details on how the serving Docker image is configured.
You can run `task serving:docker:build serving:run-docker-single` to first build a new Docker image for your models and run it on your local machine to check if all imports work as intended.
Refer to the Taskfile in `tasks/serving.yaml` for the `run-docker-single` command.

This command does the following things to enable local testing:

- It uses the `latest` tag of your serving image, meaning that it always runs the latest serving image built on your machine to enable faster iteration.
- It exposes port 8080, which is the same port that SageMaker Endpoints expect your server to listen on. You can use tools like `curl` to query your server on localhost like `curl http://localhost:8080/ping`.
- It mounts the directory `local/model` to `/opt/ml/model` in the container, which is the same directory as SageMaker puts the contents of your `model.tar.gz` file in.
You can put a local copy of your model or a smaller dummy model with the same architecture in  `local/model` to test your model loading routines.
- It shows how to set the environment variable to use different deployments with the same image.

The tasks defined there need to be adapted for your specific use case.

## Testing with SageMaker Endpoints

Once you have verified that a) your server runs locally, and b) your Docker image works as intended, you can test your model in a SageMaker endpoint.
For this purpose, you can use the tool located at `src/project/example_serving/sagemaker.py`, which you can execute by running `python -m project.example_serving.sagemaker`, in a shell with your environment activated.
To test a new version of your serving image, you need to register a model with the SageMaker Model Registry.

To avoid having to re-run a SageMaker Workflow that registers a model after training, you can instead use the `register-model` command of the tool.
First, use the command `task serving:docker:build serving:docker:push` to build and push your current serving image to the registry.
Provide the resulting image URI to the command.
If you have multiple deployments defined in your project and you want to re-use your serving image, you can override the environment variable `RAY_SERVE_RUN_ARGS` by using the `--env` flag.
This environment variable gets used by the entry point script in `scripts/serving_entrypoint.sh` to determine the `serve run` arguments at runtime.
By calling the below register command multiple times with different `--env` and `--model-data-uri` flags, you can register multiple models with different data, but re-use the same serving image.
Since only registered models that have the "Approved" status, you can provide the `--approve` flag, or manually approve the model in SageMaker studio.

```bash
python -m project.example_serving.sagemaker register-model \
    --model-package-group example-package-group \
    --model-data-uri s3://<path to existing>/model.tar.gz \
    --env RAY_SERVE_RUN_ARGS=project.example_serving.single:handle \
    --image-uri <use case container registry>/serving:<updated digest> \
    --approve
```

Once you have registered a model, you can deploy it using the `deploy-model` command.

```bash
python -m project.example_serving.sagemaker deploy-model \
    --role <SageMaker role to execute the model with> \
    <registred model package ARN>
```

This will deploy your model in a SageMaker endpoint.
If you endpoint fails to come alive as intended, the command will fail and you can check CloudWatch for the logs emitted during startup.
If your model was deployed successfully, you can visit the "Endpoints" section in SageMaker studio to submit test requests to the endpoints or use the SageMaker Python SDK to submit multiple requests.

Whenever you need to update your endpoint, you need to delete it first, as the SageMaker Python SDK currently does not support in-place updates of the endpoints.
Run the following command to delete the endpoint.

```bash
python -m project.example_serving.sagemaker delete-endpoint
```

You should **adapt the helper script** to your use case by changing the defaults and setting the endpoint name or making it settable on the CLI.
Note that **running SageMaker Endpoints incurs cost** and you should therefore keep the number of concurrently running endpoints small.
For this reason, the script has a hardcoded name for the endpoint, avoiding creating and forgetting to delete many endpoints during testing.
