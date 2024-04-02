"""
Example Spark function
"""
from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def function(df: DataFrame) -> DataFrame:
    """
    Example Spark function which adds a new column

    Args:
        df (DataFrame):

    Returns:
        DataFrame: DataFrame with "Example" column
    """
    return df.withColumn("Example", F.lit("Constant!"))
