from palitra.core import EventLoopThreadRunner


def test_non_debug(event_loop_runner: EventLoopThreadRunner) -> None:
    assert not event_loop_runner.get_loop().get_debug()


def test_debug(event_loop_runner: EventLoopThreadRunner) -> None:
    async def test() -> None:
        assert event_loop_runner.get_loop().get_debug()

    event_loop_runner.run(test(), debug=True)
