import os
import binascii
import random
from importlib import import_module


# This solution was inspired by django-rest-passwordreset package


class RandomStringTokenGenerator():
    """
    Generates a random string with min and max length using os.urandom and binascii.hexlify
    """

    def __init__(self, min_length=10, max_length=50):
        self.min_length = min_length
        self.max_length = max_length

    def generate_token(self):
        """ generates a pseudo random code using os.urandom and binascii.hexlify """
        # determine the length based on min_length and max_length
        length = random.randint(self.min_length, self.max_length)

        # generate the token using os.urandom and hexlify
        return binascii.hexlify(
            os.urandom(self.max_length)
        ).decode()[0:length]

class RandomNumberTokenGenerator():
    """
    Generates a random number using random.SystemRandom() (which uses urandom in the background)
    """
    def __init__(self, min_number=10000, max_number=99999):
        self.min_number = min_number
        self.max_number = max_number

    def generate_token(self):
        r = random.SystemRandom()

        # generate a random number between min_number and max_number
        return str(r.randint(self.min_number, self.max_number))