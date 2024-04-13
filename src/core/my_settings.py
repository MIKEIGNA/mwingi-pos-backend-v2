from mysettings.models import MySetting

def make_MySetting_query():
    
    try:
        my_setting = MySetting.objects.get(name='main')
        
    except: # pylint: disable=bare-except
        my_setting = MySetting.objects.get_or_create(name='main')
        
    return my_setting


class MySettingClass:
    @staticmethod
    def maintenance_mode():
        return make_MySetting_query().maintenance
    
    @staticmethod
    def maintenance_signup():
        query = make_MySetting_query()
        
        signup = query.signups
        maint = query.maintenance
        
        return maint, signup
    
    @staticmethod
    def maintenance_allow_contact():
        query = make_MySetting_query()
        
        maint = query.maintenance
        allow_contact = query.allow_contact
        
        return maint, allow_contact
    
    @staticmethod
    def accept_payments():
        return make_MySetting_query().accept_payments

    @staticmethod
    def accept_mpesa():
        return make_MySetting_query().accept_mpesa

    @staticmethod
    def accept_payments_and_mpesa():
        query = make_MySetting_query()
        
        allow_payments = query.accept_payments
        allow_mpesa = query.accept_mpesa
        
        return allow_payments , allow_mpesa
    
    @staticmethod
    def allow_new_employee():
        return make_MySetting_query().new_employee
    
    @staticmethod
    def allow_new_location():
        return make_MySetting_query().new_location
    
    @staticmethod
    def allow_new_product():
        return make_MySetting_query().new_product

    @staticmethod
    def allow_new_customer():
        return make_MySetting_query().new_customer
    
    @staticmethod
    def allow_new_sale():
        return make_MySetting_query().new_sale
    

    
