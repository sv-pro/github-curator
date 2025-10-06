#!/usr/bin/env python
"""Test script for Prefect pipeline - Phase 1 implementation."""

import os
import time

# Load environment variables first
from dotenv import load_dotenv

load_dotenv()

# Verify API key is loaded
if not os.getenv("ANTHROPIC_API_KEY"):
    print("❌ Error: ANTHROPIC_API_KEY not found in environment")
    print("   Please ensure .env file exists with ANTHROPIC_API_KEY=your_key")
    exit(1)

from curator.pipeline import test_intent_flow


def main():
    """Test the Prefect pipeline with caching demonstration."""
    print("=" * 70)
    print("Prefect Pipeline Test - Phase 1: Intent Structuring with Caching")
    print("=" * 70)

    theme = "AI agents with tool use"

    # First run - should execute the task
    print("\n🟦 First run (expect cache MISS - task will execute):")
    print("-" * 70)
    start_time = time.time()
    result1 = test_intent_flow(theme=theme)
    duration1 = time.time() - start_time

    print(f"\n⏱️  Duration: {duration1:.2f}s")
    print(f"📋 Result: {len(result1.dimensions)} dimensions created")

    # Second run - should hit cache
    print("\n\n🟩 Second run (expect cache HIT - should be instant):")
    print("-" * 70)
    start_time = time.time()
    result2 = test_intent_flow(theme=theme)
    duration2 = time.time() - start_time

    print(f"\n⏱️  Duration: {duration2:.2f}s")
    print(f"📋 Result: {len(result2.dimensions)} dimensions retrieved")

    # Verify cache hit
    speedup = duration1 / duration2 if duration2 > 0 else float("inf")
    print("\n" + "=" * 70)
    print("📊 Performance Analysis:")
    print(f"   First run:  {duration1:.2f}s (executed task)")
    print(f"   Second run: {duration2:.2f}s (from cache)")
    print(f"   Speedup:    {speedup:.1f}x faster")
    print(f"   Same result: {result1.intent_id == result2.intent_id}")

    if duration2 < duration1 * 0.5:
        print("\n✅ SUCCESS: Caching is working correctly!")
    else:
        print("\n⚠️  WARNING: Second run should be faster (cache may not be working)")

    # Test with different theme - should be cache miss
    print("\n\n🟨 Third run with different theme (expect cache MISS):")
    print("-" * 70)
    different_theme = "machine learning visualization tools"
    start_time = time.time()
    result3 = test_intent_flow(theme=different_theme)
    duration3 = time.time() - start_time

    print(f"\n⏱️  Duration: {duration3:.2f}s")
    print(f"📋 Result: {len(result3.dimensions)} dimensions created")
    print(f"   Different intent ID: {result3.intent_id != result1.intent_id}")

    print("\n" + "=" * 70)
    print("🎉 Test completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
