ARG BUILD_BASE=906507146617.dkr.ecr.eu-central-1.amazonaws.com/docker_base_images:python3.9-slim_gpu-20230201
ARG RUNTIME_BASE=906507146617.dkr.ecr.eu-central-1.amazonaws.com/docker_base_images:python3.9-slim_gpu-20230201

# Dedicated stage to set up the runtime environment
FROM ${BUILD_BASE} as build-environment

WORKDIR /setup

RUN python3.9 -m venv /runtime/venv

ARG REQUIREMENTS_FILE
COPY ${REQUIREMENTS_FILE} /setup/requirements.txt

ARG PIP_INDEX_URL
ARG PIP_TRUSTED_HOST
RUN --mount=type=cache,target=/root/.cache/pip \
    /runtime/venv/bin/pip install -r requirements.txt

# Dedicated stage to build just the project wheels and
# install them to the same prefix as the runtime environment
# for use with Docker COPY --link
FROM ${BUILD_BASE} as build-wheel
WORKDIR /setup

# Need to set up an empty venv with the same path
# prefix as the runtime environment for the entrypoint
# scripts to work correctly
RUN python3.9 -m venv /runtime/venv

COPY . /setup

ARG PIP_INDEX_URL
ARG PIP_TRUSTED_HOST
RUN /runtime/venv/bin/pip install . --no-deps --prefix /export/runtime/venv


FROM ${RUNTIME_BASE} as runtime-base
# Copy prepared runtime environment from build stage and
# prepend path to ensure desired project bins are available
# on the PATH
COPY --from=build-environment /runtime/venv /runtime/venv

# Link-copy the installed project wheel into the runtime image
# avoiding pulling the potentially large image containing the
# virtual environment with runtime dependencies
COPY --from=build-wheel /export/runtime/venv /runtime/venv


# Placeholder stages to enable targeting and purpose-specific
# setting of envvars, cmd, or entrypoint
FROM runtime-base as serving
ENV PATH=/runtime/venv/bin:${PATH}

# The entrypoint script will run `serve run ${RAY_SERVE_RUN_ARGS}`,
# allowing to override the servable when registring a model. This
# allows re-use of the same serving container to host multiple,
# differnt models, as long has they have the same dependencies
ENV RAY_SERVE_RUN_ARGS=project.example_serving.single:handle

# Configures Ray to emit the logs as JSON objects, which are
# better parsable by observability platforms like CloudWatch
ENV RAY_SERVE_ENABLE_JSON_LOGGING=1

# Copies the entrypoint script, enabling the overriding of
# Ray serve CLI arguments by setting the environment variable
# RAY_SERVE_RUN_ARGS defined above. This allows to re-use the
# same image for multiple, different models, as long as they
# all of their dependencies are contained in the image.
COPY scripts/serving_entrypoint.sh /runtime/entrypoint.sh
ENTRYPOINT ["./runtime/entrypoint.sh"]

FROM runtime-base as training
ENV PATH=/runtime/venv/bin:${PATH}


FROM runtime-base as processing
ENV PATH=/runtime/venv/bin:${PATH}


FROM runtime-base as spark

# Submitting Spark jobs requires stand-alone scripts
COPY ./scripts /runtime/scripts

# Add SageMaker provided Spark libraries to PYTHONPATH
ENV PYSPARK_PYTHON=/runtime/venv/bin/python
ENV PYTHONPATH="${SPARK_HOME}/python/lib/pyspark.zip:${SPARK_HOME}/python/lib/py4j-src.zip"
