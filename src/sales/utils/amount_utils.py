class AmountUtils:
    
    @staticmethod
    def calculate_total_amount(subtotal_amount, discount_rate):
        """ Calculates receipt's total amount"""

        total_amount = 0

        discount_amount = (subtotal_amount*discount_rate)/100

        if subtotal_amount > discount_amount:
            total_amount = subtotal_amount - discount_amount

        return total_amount, discount_amount