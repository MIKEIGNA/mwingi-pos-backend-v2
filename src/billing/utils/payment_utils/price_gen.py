from django.conf import settings

class PriceGeneratorClass:
    

    @staticmethod
    def account_price_discount_calc(num_of_months):
        """
        Calculates the price and discount of a tracker
    
        Parameters:
        num_of_months: number of months for tracker payment
        
        Return:
        If given the right values, it returns a tuple with price and discount eg ('1425', 5)
        If given the wrong values, it returns a tuple with zero, zero eg (0, 0) 
        """
    

        try:
            price = settings.SUBSCRIPTION_PRICES['account'] * num_of_months
            
            discount_name = '{}_months'.format(num_of_months)
            discount = settings.SUBSCRIPTION_PRICE_DISCOUNTS[discount_name]
        
            # Formula used to calculate : 25/100 * 1500
            discount_amount = (discount / 100) * price
            final_price = price - discount_amount
            
            return int(final_price), discount
        
        except:
            """
            return 0, 0 when provided with a wrong user_type or num_of_months
            """
            return 0, 0

    @staticmethod
    def account_price_calc(num_of_months):
        """
        Calculates the price of a tracker
    
        Parameters:
        num_of_months: number of months for tracker payment
        
        Return:
        If given the right values, it returns an int with the prices
        If given the wrong values, it returns an int with a zero 
        """
        return PriceGeneratorClass.account_price_discount_calc(num_of_months)[0]


    @staticmethod
    def all_accounts_price_discount_calc(num_of_months, accounts_count):
        """
        Calculates the prices and discounts of accounts
    
        Parameters:
            num_of_months: number of months for tracker payment
            accounts_count: number of accounts that are being payed for
        Return:
            If given the right values, it returns a tuple with price and discount eg ('1425', 5)
            If given the wrong values, it returns a tuple with zero, zero eg (0, 0) 
        """

        try:
            price = (settings.SUBSCRIPTION_PRICES['account'] * num_of_months) * accounts_count
            
            discount_name = '{}_months'.format(num_of_months)
            discount = settings.SUBSCRIPTION_PRICE_DISCOUNTS[discount_name]
        
            # Formula used to calculate : 25/100 * 1500
            discount_amount = (discount / 100) * price
            final_price = price - discount_amount
                    
            return int(final_price), discount
        
        except:
            """
            return 0, 0 when provided with a wrong tracker_type or num_of_months
            """
            return 0, 0

    @staticmethod
    def all_accounts_price_calc(num_of_months, accounts_count):
        """
        Calculates the prices of accounts
    
        Parameters:
            num_of_months: number of months for tracker payment
            accounts_count: number of accounts that are being payed for
        Return:
            If given the right values, it returns an int with the prices
        If given the wrong values, it returns an int with a zero 
        """
        return PriceGeneratorClass.all_accounts_price_discount_calc(num_of_months, accounts_count)[0]
