"""Wrapper script to execute the Spark program using smspark-submit.

This script is supposed to be used in SageMaker Spark Containers
and images derived from it.
Ref: https://github.com/aws/sagemaker-spark-container
"""
from project.example_spark.cli import app

if __name__ == "__main__":
    app()
