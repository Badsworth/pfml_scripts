import pytest

from massgov.pfml.util.config import get_env_bool


@pytest.mark.parametrize(
    "env_setup, env_key, expected_result, kwargs",
    [
        ({"TEST": "true"}, "TEST", True, {}),
        ({"TEST": "True"}, "TEST", True, {}),
        ({"TEST": "TRUE"}, "TEST", True, {}),
        ({"TEST": "1"}, "TEST", True, {}),
        ({"TEST": 1}, "TEST", True, {}),
        ({"TEST": "t"}, "TEST", True, {}),
        ({"TEST": "T"}, "TEST", True, {}),
        ({"TEST": "y"}, "TEST", True, {}),
        ({"TEST": "yes"}, "TEST", True, {}),
        ({"TEST": "false"}, "TEST", False, {}),
        ({"TEST": "False"}, "TEST", False, {}),
        ({"TEST": "FALSE"}, "TEST", False, {}),
        ({"TEST": "0"}, "TEST", False, {}),
        ({"TEST": 0}, "TEST", False, {}),
        ({"TEST": "f"}, "TEST", False, {}),
        ({"TEST": "F"}, "TEST", False, {}),
        ({"TEST": "n"}, "TEST", False, {}),
        ({"TEST": "no"}, "TEST", False, {}),
        ({"TEST": ""}, "TEST", None, {}),
        ({"TEST": ""}, "TEST", False, {"default": False}),
        ({"TEST": "true"}, "KEY_DOES_NOT_EXIST", None, {}),
        ({"TEST": "true"}, "KEY_DOES_NOT_EXIST", False, {"default": False}),
    ],
)
def test_get_env_bool_basics(env_setup, env_key, expected_result, kwargs, monkeypatch):
    for k, v in env_setup.items():
        monkeypatch.setenv(k, v)
    assert get_env_bool(env_key, **kwargs) == expected_result
