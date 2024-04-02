# General

## Guiding Principles

The guiding principles behind the structure and code in this repository are as follows:

- A project is developed as a shared Python library that is used by multiple Python command line applications, where each command line application governs one step of the model building process.
- The projects' dependencies are strictly managed by pip-tools to provide stable and reproducible environments.
- The projects' command line applications can be executed in the local development environment to enable quick iteration and debugging.
- The project is packaged as one or multiple Docker images, possibly for different purposes, e.g. a dedicated image for training a model, and a dedicated image for running inference.
- The local development environment has the same versions of Python and other dependencies as the Docker images built for running the code on SageMaker.
- The parity between local and remote Python environment enables local testing.
At least each command line application is covered by a unittest, running the application on example data to verify correctness before submitting a run to SageMaker.
- SageMaker pipelines are used to orchestrate the command line applications and describe dependencies between them.
SageMaker SDKs are used as a layer on top of the projects' codebase, not as a dependency.
- SageMaker pipeline steps are written in a way that they can be run either as part of a pipeline or individually to enable iteration on individual steps of the pipeline.
- Tests and code linters run in a CI system on every commit pushed to the remote Git repository.

## Directory Contents

On the top-level directory, `pyproject.toml` contains general Python project configuration for the development tools used for the project.
It also contains the dependency management, which is [described in a separate guide](dependencies.md).

`Taskfile.yaml` contains [Taskfile](https://taskfile.dev) definitions of recurring tasks that need to be run during project development.
The tasks are mostly included from the `tasks` directory, which contains the actual definitions of the Tasks.
Their use is described in the various guides on [dependency management](dependencies.md), [Docker usage](docker.md), and [serving](serving.md).

Use case, user- and machine-specific environment variables are managed in two files called `usecase.env` and `.env`.
There are examples of both of these files with comments: `usecase.env.example` and `.env.example`.
Both files are automatically included by Taskfile.
When starting a new use case or cloning the use case for the first time, rename the examples and adjust them them out according to your use case.

`src` contains the main project library and the SageMaker pipelines and step definitions.

`tests` contains the `pytest`-based tests of the projects' library and command line applications.
As the test are not intended to be shipped as part of the projects' library, they are separated out [following recommended best-practice](https://docs.pytest.org/en/7.1.x/explanation/goodpractices.html#tests-outside-application-code).

`scripts` is a place for helper scripts.
The examples provided are an entrypoint script for the serving Docker image and a wrapper script to submit Spark Jobs.

## Testing

At least the high level logic of the project should be covered by unit tests.
An example of that would be `tests/test_example_spark.py` where the business logic is tested locally using example data.
By adopting the pattern of shared project library with multiple command line applications, this pattern of testing becomes easy to implement.
In addition, critical parts of the business logic should be covered separately to cover edge cases.
For example, a parsing function that needs to support a wide variety of input formats and might be expanded in the future, is a good candidate.
This makes sure that future changes don't introduce regressions.

## Logging

Since the projects' code is running in a remote system, logging is crucial to return information about the current state of the application and catch possible bugs.

Unless you have good reason to do otherwise, a good practice is to instantiate the Python logger using `logger = logging.getLogger(__name__)` at the top of each Python module and configure the logger *once* using `logging.basicConfig(...)` in each command line application.
The command line applications in `src/` illustrate this pattern.

**Don't log into files, instead log to STDOUT or STDERR**.
This is default when using `basicConfig`.
A good explanation of this pattern is given [as part of the 12 factor app manifesto](https://12factor.net/logs).
Log messages emitted from applications running on SageMaker are aggregated into [AWS CloudWatch](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html) where they can be searched and are available even after the VMs backing the SageMaker jobs are terminated.

## Recommended Tools and Patterns

The code in this repository uses various tools to test code and aid development of the necessary command line applications.

To ensure consistent code style, we recommend the use of the [`black` code formatter](https://black.readthedocs.io/en/stable/) and [`isort`](https://pycqa.github.io/isort/) for consistent import order.
Common code-smells are caught by using [`PyLint`](https://pylint.pycqa.org/en/latest/) and [`mypy`](https://mypy.readthedocs.io/en/stable/) is used to check the validity of the type annotations used in the project.
All of these tools should be ran against any code being checked in and we have an example task definition in `Taskfile.yaml` that enables running all of these tools at once using `task tests`.

For testing we recommend the use of [`PyTest`](https://docs.pytest.org/en/7.1.x/) as it has many integration with other Python tools and enables writing unit tests with minimal boiler plate code.
We use the [`pytest-cov` plugin](https://pytest-cov.readthedocs.io/en/latest/) to generate line coverage reports.

When writing command line applications, we recommend [`Typer`](https://typer.tiangolo.com) and the use of [`PyDantic`](https://pydantic-docs.helpmanual.io) when loading configuration from structured files like JSON or YAML.
