import json
import logging
import pathlib

from pyspark.sql import SparkSession
from typer import Option, Typer

from project.example_spark.function import function

logger = logging.getLogger(__name__)
app = Typer()


@app.command()
def main(
    input_uri: str = Option(
        ...,
        help="A PySpark spark.read input URI",
    ),
    output_uri: str = Option(
        ...,
        help="A PySpark DataFrame.write.parquet-compatible output URI",
    ),
    properties_file: pathlib.Path = Option(None, help="An optional path for writing a SageMaker properties file."),
):
    logging.basicConfig(level="INFO")

    spark = SparkSession.builder.appName("Example Spark").getOrCreate()

    # Handle different sources based on URI
    if input_uri.endswith(".csv"):
        df = spark.read.csv(input_uri, sep=",", header=True)
    else:
        df = spark.read.parquet(input_uri)

    df = function(df).cache()
    df.show()

    df.write.parquet(output_uri)

    # If requested, generate a properties file to use in pipelines
    if properties_file is not None:
        properties_file.parent.mkdir(exist_ok=True, parents=True)
        properties = {"inputURI": input_uri, "outputURI": output_uri}
        properties_file.write_text(json.dumps(properties))


if __name__ == "__main__":
    app()
