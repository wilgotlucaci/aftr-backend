from utils.join_code import night_join_code, normalise_join_code


def test_join_code_is_six_upper_hex_chars():
    code = night_join_code("536f2ce8-a92c-47ac-902e-83c17e1a100e")
    assert code == "536F2C"
    assert len(code) == 6


def test_join_code_ignores_dashes_consistently():
    night_id = "b919f98e-a335-42ab-b563-84e2e3bf8640"
    assert night_join_code(night_id) == "B919F9"


def test_normalise_accepts_messy_user_input():
    assert normalise_join_code("  536f2c ") == "536F2C"
    assert normalise_join_code("536-F2C") == "536F2C"
    assert normalise_join_code("536F2CEXTRA") == "536F2C"


def test_normalise_short_input_stays_short():
    assert normalise_join_code("abc") == "ABC"
