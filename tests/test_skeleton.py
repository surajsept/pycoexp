# -*- coding: utf-8 -*-

import pytest
from pycoexp.skeleton import fib

__author__ = "Suraj Sharma"
__copyright__ = "Suraj Sharma"
__license__ = "gpl3"


def test_fib():
    assert fib(1) == 1
    assert fib(2) == 1
    assert fib(7) == 13
    with pytest.raises(AssertionError):
        fib(-10)
