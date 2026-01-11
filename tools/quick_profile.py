#!/usr/bin/env python3
"""
Quick profiling utility - add timing to specific functions.

Usage in code:
    from tools.quick_profile import profile_function, time_block
    
    # Time a function
    @profile_function
    def my_function():
        pass
    
    # Time a code block
    with time_block("expensive_operation"):
        # ... code ...
        pass
"""

import functools
import time
from typing import Callable, Optional


# Global stats
_timing_stats = {}


def profile_function(func: Callable) -> Callable:
    """
    Decorator to profile a function.
    
    Usage:
        @profile_function
        def my_function():
            pass
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        
        # Track statistics
        if func.__name__ not in _timing_stats:
            _timing_stats[func.__name__] = {
                'calls': 0,
                'total_time': 0.0,
                'min_time': float('inf'),
                'max_time': 0.0,
            }
        
        stats = _timing_stats[func.__name__]
        stats['calls'] += 1
        stats['total_time'] += elapsed
        stats['min_time'] = min(stats['min_time'], elapsed)
        stats['max_time'] = max(stats['max_time'], elapsed)
        
        # Print if over threshold (1ms)
        if elapsed > 0.001:
            print(f"[PROFILE] {func.__name__}: {elapsed*1000:.2f}ms")
        
        return result
    
    return wrapper


class time_block:
    """
    Context manager to time a code block.
    
    Usage:
        with time_block("operation_name"):
            # ... code ...
    """
    
    def __init__(self, name: str, threshold_ms: float = 1.0):
        """
        Args:
            name: Name for this timing block
            threshold_ms: Only print if time exceeds this (milliseconds)
        """
        self.name = name
        self.threshold = threshold_ms / 1000.0  # Convert to seconds
        self.start: Optional[float] = None
    
    def __enter__(self):
        self.start = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start is not None:
            elapsed = time.perf_counter() - self.start
            if elapsed > self.threshold:
                print(f"[TIMER] {self.name}: {elapsed*1000:.2f}ms")
        return False


def print_stats():
    """Print accumulated timing statistics."""
    if not _timing_stats:
        print("No timing statistics collected.")
        return
    
    print("\n=== Timing Statistics ===")
    print(f"{'Function':<30} {'Calls':<10} {'Total (ms)':<15} {'Avg (ms)':<15} {'Min (ms)':<15} {'Max (ms)':<15}")
    print("-" * 100)
    
    # Sort by total time
    sorted_stats = sorted(_timing_stats.items(), key=lambda x: x[1]['total_time'], reverse=True)
    
    for func_name, stats in sorted_stats:
        avg_time = stats['total_time'] / stats['calls'] if stats['calls'] > 0 else 0
        print(
            f"{func_name:<30} "
            f"{stats['calls']:<10} "
            f"{stats['total_time']*1000:<15.2f} "
            f"{avg_time*1000:<15.2f} "
            f"{stats['min_time']*1000:<15.2f} "
            f"{stats['max_time']*1000:<15.2f}"
        )
    
    print()


def reset_stats():
    """Reset all timing statistics."""
    global _timing_stats
    _timing_stats = {}


if __name__ == "__main__":
    # Example usage
    @profile_function
    def example_function():
        time.sleep(0.01)  # Simulate work
    
    for _ in range(5):
        example_function()
    
    with time_block("example_block"):
        time.sleep(0.005)
    
    print_stats()

