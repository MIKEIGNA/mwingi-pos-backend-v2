
class ListUtils:

    @staticmethod
    def extract_numbers_from_string(string):
        """
        Args:
            string (str): A string of numbers seperated by commas

        Returns a list of numbers
            Example if string was '1,2,3' returns [1, 2, 3]
        """
        num_list = string.split(',')

        return [reg_no for reg_no in num_list if reg_no]