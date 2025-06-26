#!/usr/bin/env python3
"""
Palitra CLI - Command Line Interface

Usage:
    python palitra_cli.py demo          # Run demo examples
    python palitra_cli.py test          # Run basic functionality test
    python palitra_cli.py info          # Show library information
"""

import sys
import asyncio
import time
from typing import List

def run_demo():
    """Run demonstration examples."""
    print("🚀 Palitra Library Demo")
    print("=" * 40)
    
    from palitra import run, gather, EventLoopThreadRunner
    
    # Demo 1: Basic usage
    print("\n1. Basic async function call:")
    async def hello():
        await asyncio.sleep(0.1)
        return "Hello from async!"
    
    result = run(hello())
    print(f"   Result: {result}")
    
    # Demo 2: Concurrent execution
    print("\n2. Concurrent execution:")
    async def process_item(item):
        await asyncio.sleep(0.1)
        return f"Processed {item}"
    
    items = ["A", "B", "C"]
    start_time = time.time()
    results = gather(*[process_item(item) for item in items])
    end_time = time.time()
    
    print(f"   Results: {results}")
    print(f"   Time: {end_time - start_time:.3f}s")
    
    # Demo 3: Context manager
    print("\n3. Context manager usage:")
    with EventLoopThreadRunner() as runner:
        result1 = runner.run(hello())
        result2 = runner.run(hello())
        print(f"   Results: {result1}, {result2}")
    
    print("\n✅ Demo completed successfully!")


def run_test():
    """Run basic functionality test."""
    print("🧪 Palitra Library Test")
    print("=" * 40)
    
    from palitra import run, gather, shutdown_global_runner, is_runner_alive
    
    try:
        # Test 1: Basic functionality
        print("\n1. Testing basic run() function:")
        async def test_function():
            await asyncio.sleep(0.1)
            return "Test passed"
        
        result = run(test_function())
        print(f"   ✅ run() test: {result}")
        
        # Test 2: Concurrent execution
        print("\n2. Testing gather() function:")
        async def test_concurrent(i):
            await asyncio.sleep(0.1)
            return f"Task {i}"
        
        results = gather(*[test_concurrent(i) for i in range(3)])
        print(f"   ✅ gather() test: {results}")
        
        # Test 3: Error handling
        print("\n3. Testing error handling:")
        async def test_error(should_fail):
            if should_fail:
                raise ValueError("Test error")
            return "Success"
        
        error_results = gather(
            test_error(False),
            test_error(True),
            test_error(False),
            return_exceptions=True
        )
        
        success_count = sum(1 for r in error_results if not isinstance(r, Exception))
        error_count = sum(1 for r in error_results if isinstance(r, Exception))
        print(f"   ✅ Error handling test: {success_count} successes, {error_count} errors")
        
        # Test 4: Runner lifecycle
        print("\n4. Testing runner lifecycle:")
        print(f"   Runner alive: {is_runner_alive()}")
        shutdown_global_runner()
        print(f"   After shutdown: {is_runner_alive()}")
        
        # Test 5: New runner creation
        result = run(test_function())
        print(f"   ✅ New runner test: {result}")
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False
    
    return True


def show_info():
    """Show library information."""
    print("📚 Palitra Library Information")
    print("=" * 40)
    
    try:
        import palitra
        print(f"Version: {getattr(palitra, '__version__', '0.0.1')}")
        print(f"Package: {palitra.__name__}")
        print(f"Description: {palitra.__doc__}")
        
        print("\nAvailable functions:")
        from palitra import run, gather, EventLoopThreadRunner, shutdown_global_runner, is_runner_alive
        print("  • run() - Execute single coroutine")
        print("  • gather() - Execute multiple coroutines concurrently")
        print("  • EventLoopThreadRunner - Core runner class")
        print("  • shutdown_global_runner() - Shutdown global runner")
        print("  • is_runner_alive() - Check runner status")
        
        print("\nPackage structure:")
        print("  • palitra.core - Core functionality")
        print("  • palitra.utils - Utilities and exceptions")
        print("  • palitra.api - High-level API")
        
        print("\nExamples:")
        print("  • python quick_start.py - Quick start guide")
        print("  • python main.py - Comprehensive examples")
        print("  • python palitra_cli.py demo - Interactive demo")
        
    except ImportError as e:
        print(f"❌ Error importing palitra: {e}")


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Palitra CLI - Command Line Interface")
        print("\nUsage:")
        print("  python palitra_cli.py demo    # Run demo examples")
        print("  python palitra_cli.py test    # Run basic functionality test")
        print("  python palitra_cli.py info    # Show library information")
        print("\nExamples:")
        print("  python quick_start.py         # Quick start guide")
        print("  python main.py               # Comprehensive examples")
        return
    
    command = sys.argv[1].lower()
    
    if command == "demo":
        run_demo()
    elif command == "test":
        success = run_test()
        sys.exit(0 if success else 1)
    elif command == "info":
        show_info()
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: demo, test, info")
        sys.exit(1)


if __name__ == "__main__":
    main() 