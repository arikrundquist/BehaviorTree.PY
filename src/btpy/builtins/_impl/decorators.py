import time
from typing import Iterator, assert_never, override

from btpy.core import BehaviorTree, NodeRegistration, NodeStatus


class _Decorator(BehaviorTree):
    @override
    def init(self) -> None:
        super().init()
        (self.__child,) = self.children()

    def child(self) -> BehaviorTree:
        """get the decorated node"""
        return self.__child

    def tick_child(self) -> NodeStatus:
        """tick the child, halting it if it succeeds or fails"""
        match status := self.child().tick():
            case NodeStatus.SUCCESS | NodeStatus.FAILURE:
                self.child().halt()

        return status


@NodeRegistration.register
class Inverter(_Decorator):
    @override
    def _do_tick(self) -> NodeStatus:
        match status := self.tick_child():
            case NodeStatus.SUCCESS:
                return NodeStatus.FAILURE

            case NodeStatus.FAILURE:
                return NodeStatus.SUCCESS

            case _:
                return status


@NodeRegistration.register
class ForceSuccess(_Decorator):
    @override
    def _do_tick(self) -> NodeStatus:
        match self.tick_child():
            case NodeStatus.RUNNING:
                return NodeStatus.RUNNING

            case _:
                return NodeStatus.SUCCESS


@NodeRegistration.register
class ForceFailure(_Decorator):
    @override
    def _do_tick(self) -> NodeStatus:
        match self.tick_child():
            case NodeStatus.RUNNING:
                return NodeStatus.RUNNING

            case _:
                return NodeStatus.FAILURE


@NodeRegistration.register
class Repeat(_Decorator):
    @override
    def init(self) -> None:
        super().init()
        self.__idx = 0

    @override
    def halt(self) -> None:
        super().halt()
        self.__idx = 0

    @override
    def _do_tick(self) -> NodeStatus:
        num_cycles = self.get("num_cycles", int).value
        if num_cycles is None or num_cycles < -1:
            return NodeStatus.FAILURE

        iterator = self.__forever() if num_cycles < 0 else range(self.__idx, num_cycles)

        for _ in iterator:
            match status := self.tick_child():
                case NodeStatus.RUNNING:
                    return NodeStatus.RUNNING

                case NodeStatus.FAILURE | NodeStatus.SKIPPED:
                    return status

                case NodeStatus.SUCCESS:
                    self.__idx = self.__idx + 1
                    continue

                case _:  # pragma: no cover
                    assert_never(self)

        return NodeStatus.SUCCESS

    def __forever(self) -> Iterator[None]:
        while True:
            yield


@NodeRegistration.register
class RetryUntilSuccessful(_Decorator):
    @override
    def _do_tick(self) -> NodeStatus:
        num_attempts = self.get("num_attempts", int).value
        if num_attempts is None or num_attempts < -1:
            return NodeStatus.FAILURE

        iterator = self.__forever() if num_attempts < 0 else range(num_attempts)

        for _ in iterator:
            match status := self.tick_child():
                case NodeStatus.RUNNING:
                    return NodeStatus.RUNNING

                case NodeStatus.SUCCESS | NodeStatus.SKIPPED:
                    return status

                case NodeStatus.FAILURE:
                    continue

                case _:  # pragma: no cover
                    assert_never(self)

        return NodeStatus.FAILURE

    def __forever(self) -> Iterator[None]:
        while True:
            yield


@NodeRegistration.register
class KeepRunningUntilFailure(_Decorator):
    @override
    def _do_tick(self) -> NodeStatus:
        match status := self.tick_child():
            case NodeStatus.FAILURE | NodeStatus.SKIPPED:
                return status

            case _:
                return NodeStatus.RUNNING


@NodeRegistration.register
class Delay(_Decorator):
    def init(self) -> None:
        super().init()
        self.__start_time: int | None = None

    @override
    def halt(self) -> None:
        super().halt()
        self.__start_time = None

    @override
    def _do_tick(self) -> NodeStatus:
        self.__start_time = self.__start_time or time.time_ns()
        delay = self.get("delay_msec", int).value
        if delay is None:
            return NodeStatus.FAILURE

        end_time = self.__start_time + delay * 1_000_000
        if time.time_ns() < end_time:
            return NodeStatus.RUNNING

        # intentionally not self.tick_child()
        return self.child().tick()


@NodeRegistration.register
class RunOnce(_Decorator):
    def init(self) -> None:
        super().init()
        self.__final_status: NodeStatus | None = None

    @override
    def _do_tick(self) -> NodeStatus:
        if self.__final_status is None:
            match status := self.tick_child():
                case NodeStatus.RUNNING:
                    return status

                case _:
                    self.__final_status = status
                    return status

        then_skip = self.get("then_skip", bool).value
        then_skip = True if then_skip is None else then_skip
        return NodeStatus.SKIPPED if then_skip else self.__final_status
