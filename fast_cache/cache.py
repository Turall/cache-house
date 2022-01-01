from helpers import cache

@cache
def test_print():
    print("OKKKKK")


if __name__ == "__main__":
    test_print()