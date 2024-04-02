# MLOps Workflows

**Outdated**

In this document we outline the required and recommended steps during different phases of a data science project following MLOps practices.

## Starting a MLOps Project

When starting a new project, you create a Git repository based on the structure of this template repository.
In addition, the required AWS infrastructure such as S3 buckets, IAM Roles, and ECR registries need to be created.
Make sure that you have multiple, separated ECR repositories when using multiple Docker images in your project.
Set up a CI pipeline to continuously run your unit tests and code checkers, ideally against every commit but at least against each pull request.
Make sure that the Docker base images and Python packages required for your project are available in your ECR and Nexus repositories.

Regarding Git branching strategy, we recommend to start with a simple PR based workflows and a single, stable main branch that can be released from at any time.
The correctness of the main branch is ensured by running your test suite and code checkers against every commit merged into the main branch.
This pattern is also known as [GitHub Flow and described in the GitHub documentation](https://docs.github.com/en/get-started/quickstart/github-flow).

## Setting up a Development Environment

To start development of the project, clone the created Git repository to your local machine and create the a folder structure based on this example repository as required.
At least create a `requirements.in` and `requirements-dev.in` file to set up your dependencies and use the commands from the `Taskfile.yaml` to set up your Python environment, compile the dependencies, and install all required packages.

Make sure to the appropriate environment variables for your project in the `Taskfile.yaml`, such as the Docker repository and project name and create a local `.env` file to contain user-specific or machine-specific environment variables.

If set up correctly, you can run `task setup:dependencies` to create your Python environment and install the dependencies.

## Exploratory Data Analysis

You can use SageMaker Studio Notebooks to create Jupyter Notebooks for exploratory data analysis and quick prototyping.
To make the developed code compatible with your projects' code base, you can use the custom Notebook Docker image built from the `Dockerfile.notebook`.

## Developing Project Features

The main part of project development will be spent developing features.
A feature in this context can be any change to the behavior of the project, including, but not limited to, changes the in the business logic, command line applications, or SageMaker components.

To start developing a feature, create a feature branch according to the agreed upon naming convention.
If your feature requires a change in dependencies, adjust the Python requirements accordingly and request packages and Docker images missing from Nexus.
[Consult the dedicated guide](dependencies.md) for detailed workflows.
Make sure to update your local development environment after changing dependencies.
In this example repository, this can be achieved by running `task setup:dependencies`.

Iterate on your feature locally using unit tests and example or generated data.
By developing locally, you can make use of debuggers and iteration speed is high.
Submitting SageMaker jobs has a very high latency and should not be used to iterate on a feature.
If your feature involves business logic, like data transformations or model training, it should be part of your projects' library.
This repositories' project library as examples for Python modules that illustrate how to implement various business logic pieces in `src/project`.

If your feature involves creating a new step in a SageMaker Workflow, first create the appropriate command line application required to run your code.
Examples for command line applications are included in the `src` folder.
These applications typically handle argument and configuration parsing, logging configuration, and loading data.
The loaded data is then handed off to functions implemented in the projects' library.
This separation of loading and processing facilitates testing, since library functions can be called with test data and example configuration during unit tests.
An example of this pattern in shown the example test for Spark code at `tests/test_example_spark.py`.
These tests also illustrate how to test your command line applications.
Writing unit tests for the command line applications should be your minimum set of tests you write, as they will test large parts of your business logic as well as your command line interface.
The latter is slow to debug once you have submitted your code to be run on SageMaker.

If necessary, create a Dockerfile for your feature, to run your code in a Docker image in SageMaker.
This example repository contains many examples of Dockerfiles.
Set up a container registry for your Docker images and create a task to build and push your Docker images to this registry, as shown in `Taskfile.yaml`.
If possible, try to build and run your Docker image locally before submitting it to SageMaker to make sure it works as intended.

If your feature is a at a state where you can receive feedback from your team members, open a pull request to have your feature eventually merged in your main branch.
You don't have to wait until you deem your feature finished.
Feedback is often easier integrated at the start of a feature than once you have settled on an implementation.
Make sure that your CI is set up to run against each commit in a pull request.
Once your feature is merged, delete your branch and start new features from the now updated main branch.

## Developing SageMaker Jobs, Steps, and Pipelines

**To be expanded**

To include your code in SageMaker Workflows, you use the SageMaker Python SDK to create a job and/or step definition and combine the step definitions to form a pipeline.
This example repository contains an example pipeline and examples for typical steps in `pipelines` and `pipelines/steps`, respectively.
The code examples are heavily commented and can serve as a starting point for writing your own jobs and steps.

The `pipelines/steps` Python package includes a few modules that hold shared functions and constants that can be re-used for multiple, different workflow steps.

Make sure that you can run steps individually without having to run the entire pipeline.
`pipelines/steps/example_training.py` shows how to include a small command line application in the Python module defining the step and how to re-use the step configuration to start a training job.

Feel free to create multiple pipelines for a project.
Especially during development, it might make sense to have a pipeline that just includes the required steps to create the training data and a separate pipeline that includes training and model registration.

Make sure to the the appropriate IAM roles and network configuration for your pipeline and step definitions.

## Testing Models with SageMaker Endpoints

**To be expanded**

Before preparing a model for staging into production, you can start a SageMaker Endpoint to test out, if a registered model starts up correctly and answers requests to the endpoint as expected.
The script `scripts/example_deploy.py` shows how to use the SageMaker SDK to start an Endpoint from the ARN of a registered model.

## Deploying Models with SageMaker Endpoints

**To be expanded**

To be repeated whenever a new model is going to be staged into production.

- If ready, submit a full pipeline run with Docker images and SageMaker pipeline definitions based on the main branch.
- If adequate, register the trained model in the model registry.
- Create a pull request in the infrastructure repository with the updated model ARN to have the trained model and required infrastructure be deployed to MDev for testing.
- Testing infrastructure in MDev is deployed.
- Perform tests against the inference infrastructure.
- If successful, create a pull request in the infrastructure repository with the updated model ARN to have the model and required infrastructure be staged to MOps Dev.
- Required artifacts (Docker image and model artifacts) are copied into MOps based on the information contained in the SageMaker model registry.
- Testing infrastructure in MDev is destroyed.
- Deployment of data pipelines for historical data (if needed)

## Deploying SageMaker Pipelines

**To be expanded**

## Retraining Models

**To be expanded**

- If applicable, stage data collected by feedback mechanism into MDev.
- If applicable, stage new data from business systems into MDev.
- Run SageMaker pipeline based on the current main branch to train a new model. If feedback data is to be integrated, create a dedicated SageMaker Job that runs as part of the pipeline, transforming the feedback data and merging it with other data to form a common training set.
- Continue with the Deployment workflow to test and stage the updated model.

## Monitoring Models

**To be expanded**

- If applicable, create a SageMaker Workflow regularly preparing newly arrived data to test the performance metrics, e.g. accuracy, F1 score, etc., of the currently deployed model.
- Develop the necessary components using the Development Workflow.
- If applicable, create a SageMaker Model Monitoring Job using the stored inputs and outputs of the currently deployed model to derive metrics quantifying model bias or concept drift.
- Create alerts against metrics with AWS CloudWatch to ensure proper performance and schedule a re-training, if necessary.
-
