"""
Test PySpark
"""
import os
import pathlib

import pytest
from pyspark.sql import SparkSession
from typer.testing import CliRunner

from project.example_spark.cli import app
from project.example_spark.function import function


@pytest.fixture(name="spark", scope="module")
def fixture_spark():
    """Create module based PySpark session"""
    os.environ["PYSPARK_PYTHON"] = ".venv/bin/python"
    os.environ["PYSPARK_DRIVER_PYTHON"] = ".venv/bin/python"
    return SparkSession.builder.appName("Example Spark Test").getOrCreate()


def test_function(spark: SparkSession):
    df = spark.createDataFrame(data=[(1, 2), (3, 4)])

    df = function(df)

    checks, *_ = df.groupby("Example").count().collect()

    assert checks["count"] == 2
    assert checks["Example"] == "Constant!"


def test_spark_cli(tmp_path: pathlib.Path):
    runner = CliRunner()
    input_path = pathlib.Path(__file__).parent / "data/example.csv"
    output_path = tmp_path / "output.parquet"
    properties_path = tmp_path / "properties.json"

    invocation = runner.invoke(
        app,
        args=[
            "--input-uri",
            str(input_path),
            "--output-uri",
            str(output_path),
            "--properties-file",
            str(properties_path),
        ],
    )

    assert invocation.exit_code == 0
    assert properties_path.exists()
    assert output_path.exists()
