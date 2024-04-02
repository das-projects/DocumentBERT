#!/bin/bash
# Bash script entrypoint to start ray serve
# and allow overriding the arguments to run
# to re-use the same container for different
# models.
# --http-host and --http-port are set as expected for SageMaker Endpoints
# Ref: https://docs.aws.amazon.com/sagemaker/latest/dg/your-algorithms-inference-code.html#your-algorithms-inference-code-container-response
set -euxo

# Start a local ray cluster. You can set RAY_NUM_CPUS to override
# the number of advertised resources when testing locally. By default
# ray advertises as many CPUs as your machine has physical cores, which
# might not be enough to deploy all deployments.
ray start ${RAY_NUM_CPUS+--num-cpus ${RAY_NUM_CPUS}} --head --disable-usage-stats --include-dashboard "false"
serve start --http-port 8080 --http-host "0.0.0.0"

exec serve run ${RAY_SERVE_RUN_ARGS}
