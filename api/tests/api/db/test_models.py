#
# Tests for massgov.pfml.api.db.models.
#

import time
import uuid

import pytest

import massgov.pfml.api.db.models


def test_uuid_gen_using_real_time():
    t0 = int(time.time())
    u = massgov.pfml.api.db.models.uuid_gen()
    t1 = int(time.time())
    time_component = u.time_low
    assert t0 <= time_component <= t1


@pytest.mark.parametrize(
    "mock_time,mock_uuid4,expected",
    [
        (1.4717, 1, 0x1000000000000000000000001),
        (0xAABBCCDD, 0x10002000300040005000600070008000, 0xAABBCCDD300040005000600070008000),
        (0x1AABBCCDD, 0x10002000300040005000600070008000, 0xAABBCCDD300040005000600070008000),
    ],
)
def test_uuid_gen_using_mocks(mock_time, mock_uuid4, expected, monkeypatch):
    monkeypatch.setattr("time.time", lambda: mock_time)
    monkeypatch.setattr("uuid.uuid4", lambda: uuid.UUID(int=mock_uuid4))
    u = massgov.pfml.api.db.models.uuid_gen()
    assert u.time_low == int(mock_time) & 0xFFFFFFFF
    assert u == uuid.UUID(int=expected)
