import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from diffy.main import main


def test_analyze_runs_without_site_packages(tmp_path):
    patch = tmp_path / "change.diff"
    patch.write_text('+ cidr_blocks = ["0.0.0.0/0"]')
    result = subprocess.run(
        [sys.executable, "-S", "-m", "diffy", "analyze", "--diff", str(patch)],
        env={**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src")},
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout)["findings"][0]["category"] == "public_ingress"


@pytest.mark.parametrize(
    "arguments",
    [
        ["search", " ", "--source-type", "policy"],
        ["search", "network", "--source-type", "policy", "--limit", "0"],
        [
            "ingest",
            "missing-document.md",
            "--source-type",
            "policy",
            "--authority",
            "example",
        ],
    ],
)
def test_cli_input_errors_are_concise(monkeypatch, capsys, arguments):
    monkeypatch.setattr(sys, "argv", ["diffy", *arguments])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    assert capsys.readouterr().err.startswith("diffy: ")
