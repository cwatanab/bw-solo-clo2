import pytest
from tr76ui import *

def test_to_co2ppm():
    assert to_co2ppm(423) == 423
    assert to_co2ppm(6596) == 5000
    assert to_co2ppm(36852) == -12

def test_to_value():
    assert to_value(1253) == 25.3
    assert to_value(695) == -30.5
    assert to_value(1923) == 92.3