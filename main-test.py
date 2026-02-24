# main-test.py
from main import Add

def test_add():
    assert Add(2, 3) == 5
    print("Test passed")