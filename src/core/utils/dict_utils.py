from decimal import Decimal


class DictUtils:

    @staticmethod
    def remove_decimal_values_with_none_from_dict(dict_data):
        return {k: Decimal('0.00') if not v else v for k, v in dict_data.items()}