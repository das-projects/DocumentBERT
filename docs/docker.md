# Docker

We use Docker images to package code for deployment and execution in SageMaker services.
Docker images are built from Dockerfiles and need to be pushed to a container registry to be used in SageMaker services.
A single project will use multiple Docker images for different purposes, e.g. training or serving.
It is fine to use a single Docker image for multiple purposes.
For example, your Docker image for training often times has all required dependencies for running pre-processing tasks.
In this case, you can use this image for both steps.

## Common Workflows

### New Image

>I want to create a new Docker image for packaging my code and dependencies

First, define a suitable subset of dependencies and compile an image-specific requirements file.
Refer to the [guide on dependency management](./dependencies.md).

Next, add an additional stage to the Dockerfile.
You can find examples of this in the Dockerfile at the root of this repository.
This stage should inherit from the stage `runtime-base` and include all additional setup that is required to run your code.
And example of this can be seen in the `spark` stage in the example Dockerfile, where we set the `PYTHONPATH` to include Spark Python package included in the SageMaker Spark Containers.
But in most cases, you only need to prepend the Python virtual environment to the `PATH` as shown for example in the `training` stage.

To have image-specific Docker tasks available, include an image specifc instance of the `docker.yaml` taskfile, located in `tasks/docker.yaml`.
You can find multiple examples of this in the `Taskfile.yaml` at the root of this repository.
The naming convention is to namespace tasks by separating them with colons.
If your image is intended for training, for example, you should include the taskfile as `training:docker`, as shown in the example Taskfile.
Set the variable `REPOSITORY_NAME` to the name that your image should have in your projects ECR repository, set `BUILD_TARGET` to the name of the stage you just created in the Dockerfile, and set `REQUIREMENTS_FILE` to the path to your image-specific requirements file, that you compiled in the first step.
You can optionally set the variable `IMAGE_SCANNING` to `true` to enable ECR image scanning to detect vulnerabilities in your Docker image.
This is especially useful for images intended to run in SageMaker endpoints.

To be able to use your images in SageMaker services, you need to create an ECR repository.
If you included the `docker.yaml` taskfile as `training:docker`, you can run the command `task training:docker:create-ecr-repository` to create the appropriate ECR repository in AWS.
After setting up the repository, you can run `task training:docker:build` and `task training:docker:push` to build and push your image.

### Training Job Configuration

> I want to use my Docker image as part of a `TrainingJob`.

First, make sure that your training code is executable as a command line script.
Define a `scripts` entrypoint in the `pyproject.toml`, pointing to a `Typer` CLI application inside your projects' source library.
You can find examples of this in the `pyproject.toml` file in this repository under the key `[project.scripts]`.
If you want to test your entrypoint and have newly added it to the `pyproject.toml`, you need to rerun `task setup:sync-dependencies`.

To use your Docker image as part of a `TrainingJob`, instantiate an `Estimator` and set the `image_uri` parameter to the registry and image you want to use.
Set the parameter `container_entry_point` to the name of the entry point you defined in the `pyproject.toml`.
An example of this can be found at `pipelines/steps/example_training.py`.

For training jobs, it is recommended to read the hyperparameters from the JSON file provided by SageMaker, which you can also create locally to perform testing.
Input and output directories should be provided as command line arguments and default to the SageMaker paths for the channels you intend to use.
An example of a CLI interface using this convention can be found at `src/project/example_model/cli.py`.

### Processing Job Configuration

> I want to use my Docker image in a `ProcessingJob`.

As for the `TrainingJob` above, ensure that your processing code is executable as a command line script.

Instantiate a `Processor` and the set `image_uri` parameter to the registry, image, and tag you want to use.
The `entrypoint` should be set to `/runtime/venv/bin/<name of entrypoint>` to ensure that the virtual environment is used.
This differs from the `TrainingJob` above, because for images being derived from SageMaker Spark Containers, we can't prepend the virtual environment to the `PATH`.

Arguments for your processing job should be supplied on the command line and can be specified in the `Processor`s `run` method.
An example of this can be seen in `pipelines/steps/example_processor.py`.

When running a Spark job in SageMaker (_not_ EMR Job), there are additional steps to be considered.
First, since your Spark job needs to be submitted using `smspark-submit`, you need to create a wrapper script for your Spark code.
An example of this can be seen in `scripts/example_spark.py`.
This script needs to be included in the Docker image for running the job.
These additional steps needed can be seen in the Dockerfile in the root of this repository.
When instantiating the `Processor`, set the `entrypoint` parameter to `["smspark-submit", "/runtime/scripts/<name of your wrapper script>"]`.
An example of this can be seen in `pipelines/steps/example_spark.py`.

### EMR Job Configuration

> I want to use a custom image in an EMR Job

*Needs contribution*

### Endpoint Configuration

> I want to use my custom image for serving a model in SageMaker endpoints.

Please refer to the section on testing with SageMaker endpoints in the [serving guide](serving.md).

### Disk Space Issues

> I'm running out of local disk space

Docker images for packaging data science and ML software can be large.
If you run out of disk space, you can run `task training:docker:cleanup` to remove all unused Docker images and caches from your system.
This assumes that you have included the Docker tasks for an image called `training` in your `Taskfile.yaml`.
Note that after cleanup, Docker image builds will take longer the first time you run them.
