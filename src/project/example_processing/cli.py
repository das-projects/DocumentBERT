import json
import logging
import pathlib

import pandas as pd
from typer import Option, Typer

from project.example_processing.function import function

logger = logging.getLogger(__name__)
app = Typer()


@app.command()
def main(
    raw_data_path: pathlib.Path = Option(
        ...,
        help="Path to raw data file",
        exists=True,
    ),
    output_dir: pathlib.Path = Option(
        ...,
        help="Output directory",
    ),
):
    output_dir.mkdir(parents=True, exist_ok=True)

    clean_data_file = "clean.parquet"
    clean_data_path = output_dir / clean_data_file

    logger.info("Preprocessing %s...", raw_data_path)
    pd.read_csv(raw_data_path).pipe(function).to_parquet(clean_data_path)

    properties_path = output_dir / "properties.json"
    logger.info("Writing properties...")
    properties_path.write_text(json.dumps({"cleanData": clean_data_file}))


if __name__ == "__main__":
    logging.basicConfig(level="INFO")
    app()
