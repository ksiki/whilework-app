import json
from typing import Final

from utils.stop_markers import get_markers


class TestStopMarkers:
    ASSETS: Final[str] = "utils.stop_markers.ASSETS"

    def test_get_markers_success(self, mocker, tmp_path):
        test_data = {
            "language1": {"category1": ["phrase1", "phrase2"]},
            "language2": {"category2": ["phrase2", "phrase3"]},
        }

        fake_file = tmp_path / "stop_markers.json"
        fake_file.write_text(json.dumps(test_data), encoding="utf-8")

        mocker.patch(self.ASSETS, tmp_path)

        result = get_markers()
        assert result == {"phrase1", "phrase2", "phrase3"}

    def test_get_markers_file_not_found(self, mocker, tmp_path):
        mocker.patch(self.ASSETS, tmp_path)

        result = get_markers()
        assert result == set()

    def test_get_markers_invalid_json(self, mocker, tmp_path):
        fake_file = tmp_path / "stop_markers.json"
        fake_file.write_text("invalid json", encoding="utf-8")

        mocker.patch(self.ASSETS, tmp_path)

        result = get_markers()
        assert result == set()

    def test_get_markers_wrong_structure(self, mocker, tmp_path):
        fake_file = tmp_path / "stop_markers.json"
        fake_file.write_text(json.dumps(["just", "a", "list"]), encoding="utf-8")

        mocker.patch(self.ASSETS, tmp_path)

        result = get_markers()
        assert result == set()


class TestDiscordRateLimiter:
    pass
