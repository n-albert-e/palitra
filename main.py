#!/usr/bin/env python3
"""
Palitra Library - Examples and Usage Guide

This file demonstrates how to use the palitra library to run async code from sync context.
Run this file to see examples in action: python main.py
"""

import asyncio
import time
from typing import List, Dict, Any

# Import the main palitra functions
from palitra import run, gather, EventLoopThreadRunner, shutdown_global_runner


def example_1_basic_usage():
    """Example 1: Basic usage with run() function."""
    print("\n=== Example 1: Basic Usage ===")
    
    async def fetch_user_data(user_id: int) -> Dict[str, Any]:
        """Simulate fetching user data from a database."""
        await asyncio.sleep(0.1)  # Simulate network delay
        return {
            "id": user_id,
            "name": f"User {user_id}",
            "email": f"user{user_id}@example.com"
        }
    
    # Run async function from sync context
    user_data = run(fetch_user_data(123))
    print(f"Fetched user data: {user_data}")


def example_2_concurrent_execution():
    """Example 2: Running multiple coroutines concurrently."""
    print("\n=== Example 2: Concurrent Execution ===")
    
    async def process_item(item: str) -> str:
        """Process a single item."""
        await asyncio.sleep(0.1)
        return f"Processed: {item}"
    
    # Create multiple coroutines
    items = ["apple", "banana", "cherry", "date"]
    coroutines = [process_item(item) for item in items]
    
    # Run them concurrently
    start_time = time.time()
    results = gather(*coroutines)
    end_time = time.time()
    
    print(f"Results: {results}")
    print(f"Time taken: {end_time - start_time:.3f}s (concurrent)")
    
    # Compare with sequential execution
    start_time = time.time()
    sequential_results = []
    for item in items:
        result = run(process_item(item))
        sequential_results.append(result)
    end_time = time.time()
    
    print(f"Sequential time: {end_time - start_time:.3f}s")
    print(f"Speedup: {(end_time - start_time) / 0.1:.1f}x faster with gather()")


def example_3_error_handling():
    """Example 3: Error handling in async operations."""
    print("\n=== Example 3: Error Handling ===")
    
    async def risky_operation(should_fail: bool) -> str:
        """An operation that might fail."""
        await asyncio.sleep(0.1)
        if should_fail:
            raise ValueError("Operation failed!")
        return "Operation succeeded"
    
    # Handle errors with return_exceptions=True
    results = gather(
        risky_operation(False),
        risky_operation(True),
        risky_operation(False),
        return_exceptions=True
    )
    
    print("Results with error handling:")
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"  Task {i}: Error - {result}")
        else:
            print(f"  Task {i}: Success - {result}")


def example_4_timeout_handling():
    """Example 4: Handling timeouts."""
    print("\n=== Example 4: Timeout Handling ===")
    
    async def long_operation() -> str:
        """An operation that takes a long time."""
        await asyncio.sleep(2.0)
        return "Operation completed"
    
    try:
        # This will timeout after 0.5 seconds
        result = run(long_operation(), timeout=0.5)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Timeout occurred: {type(e).__name__}")


def example_5_context_manager():
    """Example 5: Using EventLoopThreadRunner as context manager."""
    print("\n=== Example 5: Context Manager ===")
    
    async def simple_task() -> str:
        await asyncio.sleep(0.1)
        return "Task completed"
    
    # Using context manager (recommended)
    with EventLoopThreadRunner() as runner:
        result1 = runner.run(simple_task())
        result2 = runner.run(simple_task())
        print(f"Results: {result1}, {result2}")
    
    print("Runner automatically closed after context manager exit")


def example_6_real_world_scenario():
    """Example 6: Real-world scenario - API calls."""
    print("\n=== Example 6: Real-world Scenario ===")
    
    async def fetch_api_data(endpoint: str) -> Dict[str, Any]:
        """Simulate API call."""
        await asyncio.sleep(0.2)
        return {
            "endpoint": endpoint,
            "data": f"Data from {endpoint}",
            "timestamp": time.time()
        }
    
    async def process_api_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Process API data."""
        await asyncio.sleep(0.1)
        return {
            **data,
            "processed": True,
            "processed_at": time.time()
        }
    
    # Fetch data from multiple endpoints
    endpoints = ["/users", "/posts", "/comments"]
    fetch_coroutines = [fetch_api_data(endpoint) for endpoint in endpoints]
    
    # Fetch all data concurrently
    raw_data = gather(*fetch_coroutines)
    print(f"Fetched data from {len(raw_data)} endpoints")
    
    # Process each piece of data
    process_coroutines = [process_api_data(data) for data in raw_data]
    processed_data = gather(*process_coroutines)
    
    print("Processed data:")
    for data in processed_data:
        print(f"  {data['endpoint']}: {data['data']} (processed: {data['processed']})")


def example_7_manual_runner_management():
    """Example 7: Manual runner management."""
    print("\n=== Example 7: Manual Runner Management ===")
    
    async def worker_task(task_id: int) -> str:
        await asyncio.sleep(0.1)
        return f"Task {task_id} completed"
    
    # Create runner manually
    runner = EventLoopThreadRunner()
    
    try:
        # Run multiple tasks
        results = []
        for i in range(3):
            result = runner.run(worker_task(i))
            results.append(result)
        
        print(f"Manual runner results: {results}")
        
    finally:
        # Always close the runner
        runner.close()
        print("Manual runner closed")


def example_8_global_runner_lifecycle():
    """Example 8: Global runner lifecycle management."""
    print("\n=== Example 8: Global Runner Lifecycle ===")
    
    async def lifecycle_task() -> str:
        await asyncio.sleep(0.1)
        return "Lifecycle task completed"
    
    # First call creates the global runner
    result1 = run(lifecycle_task())
    print(f"First call: {result1}")
    
    # Subsequent calls reuse the same runner
    result2 = run(lifecycle_task())
    print(f"Second call: {result2}")
    
    # Check if runner is alive
    from palitra import is_runner_alive
    print(f"Runner alive: {is_runner_alive()}")
    
    # Shutdown the global runner
    shutdown_global_runner()
    print("Global runner shutdown")
    print(f"Runner alive: {is_runner_alive()}")
    
    # Next call will create a new runner
    result3 = run(lifecycle_task())
    print(f"After shutdown: {result3}")


def main():
    """Run all examples."""
    print("🚀 Palitra Library Examples")
    print("=" * 50)
    
    try:
        example_1_basic_usage()
        example_2_concurrent_execution()
        example_3_error_handling()
        example_4_timeout_handling()
        example_5_context_manager()
        example_6_real_world_scenario()
        example_7_manual_runner_management()
        example_8_global_runner_lifecycle()
        
        print("\n✅ All examples completed successfully!")
        print("\n💡 Key Takeaways:")
        print("  • Use run() for single async operations")
        print("  • Use gather() for concurrent operations")
        print("  • Use context managers for automatic cleanup")
        print("  • Handle timeouts and errors appropriately")
        print("  • Global runner is automatically managed")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        shutdown_global_runner()


if __name__ == "__main__":
    main() 