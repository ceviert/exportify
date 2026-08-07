from utils.json_controller import (
    save_to_file,
    load_from_file,
    substract_the_database_from,
    merge_with_old_database,
)


def _playlist(tracks):
    return {"playlist_name": "Test", "track_count": len(tracks), "tracks": tracks}


def test_save_and_load_roundtrip(tmp_path):
    cache_file = tmp_path / "cache.json"
    data = {"id1": "video1", "id2": "video2"}
    save_to_file(data, str(cache_file))
    assert load_from_file(str(cache_file)) == data


def test_load_missing_file_returns_empty(tmp_path):
    assert load_from_file(str(tmp_path / "nope.json")) == {}


def test_load_corrupt_json_returns_empty(tmp_path):
    cache_file = tmp_path / "cache.json"
    cache_file.write_text("{not valid json")
    assert load_from_file(str(cache_file)) == {}


def test_subtract_keeps_only_new_tracks(tmp_path):
    cache_file = tmp_path / "cache.json"
    save_to_file({"id1": "v1"}, str(cache_file))
    tracks = [{"id": "id1", "name": "A"}, {"id": "id2", "name": "B"}]
    refined = substract_the_database_from(_playlist(tracks), str(cache_file))
    assert [t["id"] for t in refined] == ["id2"]


def test_subtract_empty_database_keeps_all(tmp_path):
    cache_file = tmp_path / "cache.json"
    save_to_file({}, str(cache_file))
    tracks = [{"id": "id1", "name": "A"}]
    refined = substract_the_database_from(_playlist(tracks), str(cache_file))
    assert [t["id"] for t in refined] == ["id1"]


def test_merge_combines_old_and_new(tmp_path):
    cache_file = tmp_path / "cache.json"
    save_to_file({"old": "v_old"}, str(cache_file))
    merged = merge_with_old_database({"new": "v_new"}, str(cache_file))
    assert merged == {"old": "v_old", "new": "v_new"}


def test_merge_overwrites_existing_mapping(tmp_path):
    cache_file = tmp_path / "cache.json"
    save_to_file({"id1": "v_old"}, str(cache_file))
    merged = merge_with_old_database({"id1": "v_new"}, str(cache_file))
    assert merged == {"id1": "v_new"}
