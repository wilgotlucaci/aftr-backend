from utils.storage import EXTENSION_BY_TYPE, storage_path


def test_storage_path_layout_and_extension():
    path = storage_path("night-1", "user-9", "image/jpeg")
    prefix, filename = path.rsplit("/", 1)

    assert prefix == "night-1/user-9"
    assert filename.endswith(".jpg")
    assert len(filename) == 32 + len(".jpg")  # 32 hex chars + extension


def test_unknown_type_falls_back_to_bin():
    assert storage_path("n", "u", "application/zip").endswith(".bin")


def test_known_types_have_extensions():
    for content_type, ext in EXTENSION_BY_TYPE.items():
        assert storage_path("n", "u", content_type).endswith(f".{ext}")


def test_paths_are_unique():
    paths = {
        storage_path("n", "u", "image/png") for _ in range(50)
    }
    assert len(paths) == 50
