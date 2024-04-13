from django.core.exceptions import ValidationError

        
def validate_phone_for_forms_n_serializers(
    phone, validation_error_to_raise, safaricom_only=False):
    """
    Raise a ValidationError or serializers.ValidationError if the phone 
    is incorrect.

    If "safaricom_only" is True, a ValidationError or serializers.ValidationError
    will be raised if the phone is not a correct safaricom number.

    Parameters:
        phone: int number to be verified
        validation_error_to_raise: Error instance to raise. It can be 
            ValidationError or serializers.ValidationError
        safaricom_only (boolean): - A flag indicatng if we shold also check if
            the phone is a correct safaricom phone
          
    """
    
    if len(str(phone)) < 12:
        msg = 'This phone is too short.'
        raise validation_error_to_raise(msg)
        
    elif len(str(phone)) > 12:
        msg = 'This phone is too long.'
        raise validation_error_to_raise(msg)

    if safaricom_only:
        # Check if it's a safaricom phone
        if not str(phone).startswith('2547') or not int(str(phone)[4]) in [0,1,2,9]:
            msg = 'Please Enter a Safaricom Phone That Starts With 254.'
            raise validation_error_to_raise(msg)
                 
def validate_phone_for_models(phone):
    """
    Used as a phone validator in models
    
    Raise a ValidationError if the phone is not correct. 
    
    Parameters:
          phone: int number to be verified
    """
    validate_phone_for_forms_n_serializers(phone, ValidationError)
    
    
def validate_safaricom_number(phone):
    """
    Used to validate phones in views, functions and classes
    
    Returns true if phone is a correct safaricom number and False
    otherwise
    
    Parameters:
          phone: int number to be verified
          
    Return:
        Boolean
    """
    try:
        validate_phone_for_forms_n_serializers(
            phone, ValidationError, safaricom_only=True)
        
        return True
    except:
        return False
    

def validate_percentage(value):
    """
    
    Returns true if value is not bigger than 100 and false otherwise
    
    Parameters:
          value: Decimal number to be verified
          
    Return:
        Boolean
    """
    if value > 100:
        msg = 'This value cannot be bigger than 100.'
        raise ValidationError(msg)

def validate_code(value):
    """
    
    Returns true if value is a correct color code and false otherwise
    
    Parameters:
          code: A color code
          
    Return:
        Boolean
    """

    if value.startswith('#'):
        return True

    else:
        msg = 'Wrong color code.'
        raise ValidationError(msg)
  
