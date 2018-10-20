import logging
import time
from typing import Dict

import dataclasses as dataclasses
import pytest

from auto_init import AutoInitContext


@pytest.fixture
def ctx():
    return AutoInitContext()


class Timer:
    def sleep(self, seconds: int):
        raise NotImplementedError()


class DefaultTimer(Timer):
    def sleep(self, seconds: int):
        time.sleep(seconds)


class RunLoop:
    timer: Timer
    first_sleep: int
    sleep: int
    max_iterations: int = None
    timeout: int = None


def test_initialises_based_on_type_hints(ctx):
    run_loop = RunLoop()

    ctx.init_instance(run_loop)
    assert isinstance(run_loop.timer, Timer)
    assert run_loop.first_sleep == 0
    assert run_loop.sleep == 0
    assert run_loop.max_iterations is None
    assert run_loop.timeout is None


def test_does_not_overwrite_initialised_attributes(ctx):
    run_loop = RunLoop()
    run_loop.sleep = 5

    ctx.init_instance(run_loop)
    assert run_loop.sleep == 5


def test_custom_provider(ctx):
    assert not isinstance(ctx.get_instance(Timer), DefaultTimer)

    ctx.register_factory(Timer, DefaultTimer)
    assert isinstance(ctx.get_instance(Timer), DefaultTimer)

    run_loop = RunLoop()
    ctx.init_instance(run_loop)
    assert isinstance(run_loop.timer, DefaultTimer)

    run_loop2: RunLoop = ctx.get_instance(RunLoop)
    assert isinstance(run_loop2.timer, DefaultTimer)


def test_initialises_dataclass(ctx):
    @dataclasses.dataclass
    class Point:
        x: float
        y: float
        z: float = None
        tags: Dict = dataclasses.field(default_factory=dict)

    p = ctx.get_instance(Point)
    assert p.x == 0.0
    assert p.y == 0.0
    assert p.z is None
    assert p.tags == {}


def test_registered_singleton(ctx):
    ctx.register_singleton(Timer, DefaultTimer)
    timer1 = ctx.get_instance(Timer)
    timer2 = ctx.get_instance(Timer)
    assert timer1 is timer2
    assert isinstance(timer1, DefaultTimer)


def test_registered_factory(ctx):
    ctx.register_factory(Timer, DefaultTimer)
    timer1 = ctx.get_instance(Timer)
    timer2 = ctx.get_instance(Timer)
    assert timer1 is not timer2
    assert isinstance(timer1, DefaultTimer)


def test_registered_instance(ctx):
    class WithLogger:
        log: logging.Logger

    logger = logging.Logger(__name__)
    ctx.register_instance(logger)

    a: WithLogger = ctx.get_instance(WithLogger)
    assert a.log is logger

    b: WithLogger = ctx.get_instance(WithLogger)
    assert a.log is b.log
