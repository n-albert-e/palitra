"""Integration tests for asgiref compatibility."""

import asyncio
import functools
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Any
import random
import pytest

from asgiref.sync import iscoroutinefunction, sync_to_async
from asgiref.timeout import timeout

from palitra import run


def async_to_sync(func):
    """Convert async function to sync using palitra."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return run(func(*args, **kwargs))
    return wrapper



class TestAsgirefCompatibility:
    """Test suite for asgiref compatibility."""


    @pytest.mark.asyncio
    async def check_penis_size(self) -> None:
        penis_size = random.randint(6, 20)
        assert penis_size > 13

    @pytest.mark.asyncio
    async def test_sync_to_async(self) -> None:
        """Test sync_to_async with palitra integration."""
        def sync_function() -> int:
            time.sleep(1)
            return 42

        async_function = sync_to_async(sync_function)
        start = time.monotonic()
        result = await async_function()
        end = time.monotonic()
        assert result == 42
        assert end - start >= 1

        # Test with limited workers
        loop = asyncio.get_running_loop()
        old_executor = loop._default_executor or ThreadPoolExecutor()
        loop.set_default_executor(ThreadPoolExecutor(max_workers=1))
        try:
            start = time.monotonic()
            await asyncio.wait([
                asyncio.create_task(async_function()),
                asyncio.create_task(async_function()),
            ])
            end = time.monotonic()
            assert end - start >= 2
        finally:
            loop.set_default_executor(old_executor)

    def test_sync_to_async_fail_non_function(self) -> None:
        """Test sync_to_async error handling."""
        with pytest.raises(TypeError) as excinfo:
            sync_to_async(1)

        assert excinfo.value.args == (
            "sync_to_async can only be applied to sync functions.",
        )

    @pytest.mark.asyncio
    async def test_sync_to_async_fail_async(self) -> None:
        """Test sync_to_async with async function."""
        with pytest.raises(TypeError) as excinfo:
            @sync_to_async
            async def test_function() -> None:
                pass

        assert excinfo.value.args == (
            "sync_to_async can only be applied to sync functions.",
        )

    @pytest.mark.asyncio
    async def test_sync_to_async_raises_typeerror_for_async_callable_instance(self) -> None:
        """Test sync_to_async with async callable instance."""
        class CallableClass:
            async def __call__(self) -> None:
                return None

        with pytest.raises(
            TypeError, match="sync_to_async can only be applied to sync functions."
        ):
            sync_to_async(CallableClass())

    @pytest.mark.asyncio
    async def test_sync_to_async_decorator(self) -> None:
        """Test sync_to_async as decorator."""
        @sync_to_async
        def test_function() -> int:
            time.sleep(1)
            return 43

        result = await test_function()
        assert result == 43

    @pytest.mark.asyncio
    async def test_nested_sync_to_async_retains_wrapped_function_attributes(self) -> None:
        """Test that function attributes are preserved."""
        def enclosing_decorator(attr_value):
            @wraps(attr_value)
            def wrapper(f):
                f.attr_name = attr_value
                return f
            return wrapper

        @enclosing_decorator("test_name_attribute")
        @sync_to_async
        def test_function() -> None:
            pass

        assert test_function.attr_name == "test_name_attribute"
        assert test_function.__name__ == "test_function"

    @pytest.mark.asyncio
    async def test_sync_to_async_method_decorator(self) -> None:
        """Test sync_to_async on methods."""
        class TestClass:
            @sync_to_async
            def test_method(self) -> int:
                time.sleep(1)
                return 44

        instance = TestClass()
        result = await instance.test_method()
        assert result == 44

    @pytest.mark.asyncio
    async def test_sync_to_async_method_self_attribute(self) -> None:
        """Test sync_to_async preserves method self attribute."""
        class TestClass:
            def test_method(self) -> int:
                time.sleep(0.1)
                return 45

        instance = TestClass()
        method = sync_to_async(instance.test_method)
        result = await method()
        assert result == 45

    @pytest.mark.asyncio
    async def test_async_to_sync_to_async(self) -> None:
        """Test async_to_sync to async conversion."""
        @async_to_sync
        async def inner_async_function() -> str:
            await asyncio.sleep(0.1)
            return "async result"

        @sync_to_async
        def sync_function() -> str:
            return inner_async_function()

        result = await sync_function()
        assert result == "async result"

    @pytest.mark.asyncio
    async def test_async_to_sync_to_async_decorator(self) -> None:
        """Test async_to_sync to async conversion with decorators."""
        @async_to_sync
        async def inner_async_function() -> str:
            await asyncio.sleep(0.1)
            return "async result"

        @sync_to_async
        def sync_function() -> str:
            return inner_async_function()

        result = await sync_function()
        assert result == "async result"

    @pytest.mark.asyncio
    @pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9")
    async def test_async_to_sync_to_thread_decorator(self) -> None:
        """Test async_to_sync with thread decorator."""
        @async_to_sync
        async def inner_async_function() -> str:
            await asyncio.sleep(0.1)
            return "async result"

        result = inner_async_function()
        assert result == "async result"

    def test_async_to_sync(self) -> None:
        """Test async_to_sync basic functionality."""
        @async_to_sync
        async def inner_async_function() -> str:
            await asyncio.sleep(0.1)
            return "async result"

        result = inner_async_function()
        assert result == "async result"

    def test_async_to_sync_decorator(self) -> None:
        """Test async_to_sync as decorator."""
        @async_to_sync
        async def test_function() -> str:
            await asyncio.sleep(0.1)
            return "async result"

        result = test_function()
        assert result == "async result"

    def test_async_to_sync_method_decorator(self) -> None:
        """Test async_to_sync on methods."""
        class TestClass:
            @async_to_sync
            async def test_function(self) -> str:
                await asyncio.sleep(0.1)
                return "async result"

        instance = TestClass()
        result = instance.test_function()
        assert result == "async result"

    def test_async_to_sync_in_thread(self) -> None:
        """Test async_to_sync in separate thread."""
        @async_to_sync
        async def test_function() -> str:
            await asyncio.sleep(0.1)
            return "async result"

        def thread_target() -> None:
            result = test_function()
            assert result == "async result"

        import threading
        thread = threading.Thread(target=thread_target)
        thread.start()
        thread.join()

    def test_async_to_sync_in_except(self) -> None:
        """Test async_to_sync in exception handler."""
        @async_to_sync
        async def test_function() -> str:
            await asyncio.sleep(0.1)
            return "async result"

        try:
            raise ValueError("test")
        except ValueError:
            result = test_function()
            assert result == "async result"

    def test_async_to_sync_partial(self) -> None:
        """Test async_to_sync with partial functions."""
        @async_to_sync
        async def inner_async_function(*args) -> tuple:
            await asyncio.sleep(0.1)
            return args

        partial_function = functools.partial(inner_async_function, 42)
        result = partial_function()
        assert result == (42,)

    def test_async_to_sync_on_callable_object(self) -> None:
        """Test async_to_sync on callable objects."""
        class CallableClass:
            async def __call__(self, value: str) -> str:
                await asyncio.sleep(0.1)
                return f"processed {value}"

        callable_instance = CallableClass()
        wrapped = async_to_sync(callable_instance)
        result = wrapped("test")
        assert result == "processed test"

    def test_sync_to_async_detected_as_coroutinefunction(self) -> None:
        """Test that sync_to_async functions are detected as coroutines."""
        def sync_func() -> str:
            return "sync"

        async_func = sync_to_async(sync_func)
        assert iscoroutinefunction(async_func)

    @pytest.mark.asyncio
    async def test_sync_to_async_uses_executor(self) -> None:
        """Test that sync_to_async works correctly."""
        def sync_func() -> str:
            return "executor test"

        async_func = sync_to_async(sync_func)
        result = await async_func()
        assert result == "executor test"

    def test_async_to_sync_overlapping_kwargs(self) -> None:
        """Test async_to_sync with overlapping kwargs."""
        @async_to_sync
        async def test_function(**kwargs: Any) -> None:
            await asyncio.sleep(0.01)
            assert kwargs == {"test": "value"}

        test_function(test="value")

    @pytest.mark.asyncio
    async def test_sync_to_async_overlapping_kwargs(self) -> None:
        """Test sync_to_async with overlapping kwargs."""
        @sync_to_async
        def test_function(**kwargs: Any) -> None:
            assert kwargs == {"test": "value"}

        await test_function(test="value") 