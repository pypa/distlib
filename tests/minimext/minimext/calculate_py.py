# Copyright (C) 2024 Stewart Miles
# Licensed to the Python Software Foundation under a contributor agreement.
# See LICENSE.txt and CONTRIBUTORS.txt.

"""Python implementation of the calculate extension module."""

def fib(index):
    """Calculate a Fibonacci number.

    :param index: Index of the number in the Fibonacci sequence
      to calculate.

    :returns: Fibonacci number at the specified index.
      For example an index of 7 will return 13
    """
    current_value = 1
    previous_value = 0
    index -= 1
    while index > 0:
        next_value = current_value + previous_value
        previous_value = current_value
        current_value = next_value
        index -= 1
    return current_value
