import pytest

from auto_init import AutoInitContext


@pytest.fixture
def ctx() -> AutoInitContext:
    return AutoInitContext()
