import importlib

from utils import apns


def test_not_configured_without_env_vars(monkeypatch):
    monkeypatch.setattr(apns, "APNS_KEY_ID", None)
    monkeypatch.setattr(apns, "APNS_TEAM_ID", None)
    monkeypatch.setattr(apns, "APNS_AUTH_KEY", None)

    assert apns.is_configured() is False


def test_configured_with_all_three_env_vars(monkeypatch):
    monkeypatch.setattr(apns, "APNS_KEY_ID", "key-id")
    monkeypatch.setattr(apns, "APNS_TEAM_ID", "team-id")
    monkeypatch.setattr(apns, "APNS_AUTH_KEY", "-----BEGIN PRIVATE KEY-----")

    assert apns.is_configured() is True


def test_reference_date_offset_matches_swifts_date_epoch():
    # 2001-01-01T00:00:00Z minus 1970-01-01T00:00:00Z, in seconds - this is
    # the constant Foundation's default `Date` Codable conformance uses.
    # Getting this wrong would silently corrupt `startedAt` on every push.
    assert apns._SWIFT_REFERENCE_DATE_OFFSET == 978_307_200


def test_module_reloads_env_vars_at_import_time(monkeypatch):
    monkeypatch.setenv("APNS_KEY_ID", "from-env")
    reloaded = importlib.reload(apns)

    assert reloaded.APNS_KEY_ID == "from-env"

    # Leave the module in its normal (unconfigured-in-tests) state for
    # any other test that imports it after this one.
    monkeypatch.delenv("APNS_KEY_ID", raising=False)
    importlib.reload(apns)
