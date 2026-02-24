from main import Add

def test_add():
    assert Add(6, 5) == 13  # This is intentionally wrong!

if __name__ == "__main__":
    test_add()
    print("Test passed!")
