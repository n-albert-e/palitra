#!/usr/bin/env python3
"""
Quick Start Guide for Palitra Library

This script shows the most common usage patterns in a concise way.
"""

import asyncio
from palitra import run, gather

# Example 1: Simple async function call
async def hello_world():
    await asyncio.sleep(0.1)
    return "Hello from async!"

result = run(hello_world())
print(f"Result: {result}")

# Example 2: Concurrent execution
async def process_item(item):
    await asyncio.sleep(0.1)
    return f"Processed {item}"

items = ["A", "B", "C"]
results = gather(*[process_item(item) for item in items])
print(f"Concurrent results: {results}")

print("✅ Quick start completed!") 