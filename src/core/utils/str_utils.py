from string import ascii_lowercase

LETTERS = {letter: str(index) for index, letter in enumerate(ascii_lowercase, start=1)}

class StrUtils:

    @staticmethod
    def alphabet_position(text):
        text = text.lower()

        numbers = [LETTERS[character] for character in text if character in LETTERS]

        return ' '.join(numbers)

    @staticmethod
    def letters_from_number(number):
        num_str = str(number)

        letters = [ascii_lowercase[int(num)] for num in num_str]

        return ''.join(letters)