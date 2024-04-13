from django.core.exceptions import ValidationError

class OverridePostgresLongNumberError:
    
    def add_error(self, field, error):
        """
        When using postgresql, when a user enters a very long number on a BigIntegerField
        it raises the following error:
            "Ensure this value is less than or equal to 9223372036854775807."
            
        This error is not so user friendly so we override it so that we just raise
        "This number is too long" error
        """
        
        if "9223372036854775807" in str(error):
            error = ValidationError('This number is too long.')
            
        super(OverridePostgresLongNumberError, self).add_error(field, error)