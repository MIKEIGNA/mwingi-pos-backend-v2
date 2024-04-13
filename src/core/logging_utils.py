
def clean_logging_fields(fields_dict):
    """
    Remove passwords from the dict
    """
    
    
    """ If fields_dict has 'csrfmiddlewaretoken', remove it """
    fields_dict.pop('csrfmiddlewaretoken') if fields_dict.get('csrfmiddlewaretoken', None) else ''
    
                
    """
    If passwords are in the fields_dict, replace them with *************
    to avoid real passwords being logged
    """
    if fields_dict.get('password', None):
        fields_dict['password'] = '*********'
            
    if fields_dict.get('password1', None):
        fields_dict['password1'] = '*********'
        
    if fields_dict.get('password2', None):
        fields_dict['password2'] = '*********'
    
    
    return fields_dict
    