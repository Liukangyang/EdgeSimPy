import unittest


class SimulationTestCase(unittest.TestCase):
    def test_setUp(self):
        print("SetUp")

    def test_hello(self):
        print("Hello")


if __name__ == '__main__':
    unittest.main()

