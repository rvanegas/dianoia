class ArgumentsWithStep():
    """arguments with a specific step indicated by position"""
    index: int

    # this is a special pydantic method
    def model(self):
        assert self.index == 0

