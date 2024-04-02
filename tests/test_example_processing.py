import pathlib

from typer.testing import CliRunner

from project.example_processing.cli import app


def test_example_processing(tmp_path: pathlib.Path):
    raw_data_path = pathlib.Path(__file__).parent / "data/example.csv"
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "--raw-data-path",
            str(raw_data_path),
            "--output-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0
    assert (tmp_path / "clean.parquet").exists()
