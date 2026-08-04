class Assertions:
    @staticmethod
    def is_true(value, message="Expected value to be True"):
        assert value, message

    @staticmethod
    def equals(actual, expected):
        assert actual == expected, f"Expected '{expected}', but found '{actual}'"

    @staticmethod
    def contains(actual, expected):
        assert expected in actual, f"'{expected}' not found in '{actual}'"

    @staticmethod
    def not_empty(value):
        assert value, "Value is empty"
