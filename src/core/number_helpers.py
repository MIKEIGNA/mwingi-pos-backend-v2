from decimal import Decimal


class NumberHelpers:

    # TODO #39 Replace all uses of round with this method and test this
    @staticmethod
    def normal_round(num, ndigits=2):
        """
        Rounds a float to the specified number of decimal places.
        num: the value to round
        ndigits: the number of digits to round to
        """
  
        if ndigits == 0:
            float_fmt =int(Decimal(num) + Decimal(0.5))

            return round(Decimal(float_fmt), ndigits)
        else:
            digit_value = 10 ** ndigits

            float_fmt = int(Decimal(num) * Decimal(digit_value) + Decimal(0.5)) / digit_value

            return round(Decimal(float_fmt), ndigits)

