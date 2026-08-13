import os

from backend.database import resolve_data_dir


def test_resolve_data_dir_prefers_programdata(monkeypatch, tmp_path):
    programdata = tmp_path / "ProgramData"
    appdata = tmp_path / "AppData"
    programdata.mkdir(parents=True, exist_ok=True)
    appdata.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("PROGRAMDATA", str(programdata))
    monkeypatch.setenv("APPDATA", str(appdata))
    monkeypatch.delenv("GRAFIOS_VICTORTRUCKS_DATA_DIR", raising=False)

    resolved = resolve_data_dir()

    assert resolved == os.path.join(str(programdata), "GraficosVictorTrucks")
