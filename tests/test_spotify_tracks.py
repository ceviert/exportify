from spotify.tracks import track_to_dict


def _item(track):
    return {"track": track}


def _normal_track():
    return {
        "id": "abc123",
        "name": "Rooster",
        "artists": [{"name": "Alice In Chains"}],
        "album": {"name": "Dirt", "images": [{"url": "http://img/1.jpg"}]},
        "duration_ms": 370000,
    }


def test_normal_track():
    assert track_to_dict(_item(_normal_track())) == {
        "id": "abc123",
        "name": "Rooster",
        "artist_name": "Alice In Chains",
        "album_name": "Dirt",
        "cover_url": "http://img/1.jpg",
        "duration_ms": 370000,
    }


def test_multiple_artists_joined():
    track = _normal_track()
    track["artists"] = [{"name": "Alice In Chains"}, {"name": "Layne Staley"}]
    assert track_to_dict(_item(track))["artist_name"] == "Alice In Chains, Layne Staley"


def test_missing_artists_does_not_crash():
    # Local files / podcast episodes can omit the artists key entirely.
    track = _normal_track()
    del track["artists"]
    assert track_to_dict(_item(track))["artist_name"] == ""


def test_missing_album():
    track = _normal_track()
    del track["album"]
    result = track_to_dict(_item(track))
    assert result["album_name"] == ""
    assert result["cover_url"] is None


def test_missing_album_images():
    track = _normal_track()
    track["album"] = {"name": "Dirt", "images": []}
    assert track_to_dict(_item(track))["cover_url"] is None


def test_none_track_returns_none():
    # Unavailable/region-restricted entries come through with track == None.
    assert track_to_dict(_item(None)) is None


def test_track_without_id_returns_none():
    track = _normal_track()
    del track["id"]
    assert track_to_dict(_item(track)) is None


def test_non_dict_item_returns_none():
    assert track_to_dict(None) is None
    assert track_to_dict("not a dict") is None
