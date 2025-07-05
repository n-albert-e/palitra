"""Will this even work?"""

import asyncio
from typing import Union

from palitra._global import _get_runner  # type: ignore


class _PalitraPolicy(asyncio.DefaultEventLoopPolicy):  # type: ignore
    _loop_factory = _get_runner().get_loop

    def get_event_loop(self) -> asyncio.AbstractEventLoop:
        return _get_runner().get_loop()

    def set_event_loop(
        self, loop: Union[asyncio.AbstractEventLoop, None]
    ) -> None: ...  # noop
