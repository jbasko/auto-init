import logging

from auto_init import AutoInitContext


class Worker:
    enterprise: "Enterprise"
    log: logging.Logger


class Reporter:
    enterprise: "Enterprise"
    log: logging.Logger


class Enterprise:
    worker: Worker
    reporter: Reporter


ctx = AutoInitContext()
ctx.register_instance(logging.getLogger(__name__))
ctx.register_singleton(Enterprise)

enterprise: Enterprise = ctx.get_instance(Enterprise)
assert enterprise.worker.log is enterprise.reporter.log
assert enterprise.worker.enterprise is enterprise
assert enterprise.reporter.enterprise is enterprise
