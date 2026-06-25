def test_only_enabled_directory_is_built():
    from src.repository import indexes

    assert list(indexes) == ["busybar-firmware"]


def test_import_without_github_credentials_does_not_crash():
    # the registry is built with no GitHub tokens in the test env; this must not
    # raise because the GitHub login is performed lazily (only on reindex)
    from src import repository

    assert "busybar-firmware" in repository.indexes
