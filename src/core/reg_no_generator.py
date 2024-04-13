import random
import datetime

from django.utils.crypto import get_random_string


def generate_random_number():
    """
    We use a ('one' - 'hundred billion') to make this random number more robust
    and extremly unique
    """
    return random.randint(1, 100000000000)

def get_unique_reg_no():

    random_number = generate_random_number()
    
    reg_no = GetUniqueId(random_number).get_unique_id()

    return reg_no
    
class GetUniqueId():
    """
    Returns a unique number.
    
    When time_units is in 'micros', we can get 1000 unique numbers in every 
    second.
    
    This Algorithim can work forever but we have calculated that between now 
    and year 2200 the returned number wont surpass 6000000000000 (6 000 000 000 000).
    So when you want to validate this number in your models, we can safely use a 
    max value of 6000000000000
    """
    def __init__(self, value1, value2=0, time_units='micros', days=0):
        
        self.value1 = value1
        
        if not value2 == 0:
            self.value2 = value2
        else:
            self.value2 = generate_random_number()
            
        self.time_units = time_units
        self.days = days
        
    def get_unique_id(self):
        try:
            time = self.epoch()
            
            if time:
                 
                value1 = self.value1
                value2 = self.value2
                
                value1+=generate_random_number()
                value2+=generate_random_number()
                
                # value1 and value2 are used to add randomity in the unique_id
                unique_id = int(time + value1 + value2)
                
                return unique_id
            else:
                return False
        
        except:
            return False
    
    def epoch(self):
        time_units = self.time_units # Time units can be 'minutes, seconds or micro(microseconds)'
        days = self.days # This is optional.
        
        days_millis = days*(24*60*60)
    
        start = datetime.datetime(2018, 1, 1, 00, 00, 00, 0)
        now = datetime.datetime.now()
        #now = datetime.datetime(2200, 1, 21, 13, 00, 15, 897078)
        
        # Calculate the total seconds between now and the start time of epoch 
        diff = (now - start).total_seconds() + days_millis
        diff = int(diff)
    
        if time_units == 'minutes':
            return int(diff/60) # Return time in minutes
        
        elif time_units == 'seconds':
            return diff  # Return time in seconds
        
        elif time_units == 'micros':
            return diff*1000  # Return time in microseconds
        
        else:
            """ Return False if the provided time units is wrong """
            return False

    
def GetUniqueStringForProfileNotificationGroupName():            
            
    """
    Generates a unique string for the given model
    
    Incase of a non-unique string being returned, this function will try
    again 10 times before it gives up. This is to make it nearly impossible
    to return a non-unique string for the given model. 
    """
    from profiles.models import Profile
    
    
    for i in range(10):
        secret_key = get_random_string(39)
        
        model_exists = Profile.objects.filter(notifications_group_channlel_name=secret_key).exists()
        
        
        if not model_exists:
            break
        
    return secret_key
            
def GetUniqueRegNoForModel(model):

    """
    Generates a unique reg no the given model
    
    Incase of a non-unique reg_no being returned, this function will try
    again 10 times before it gives up. This is to make it nearly impossible
    to return a non-unique reg_no for the given model. 
    """
    for i in range(10):
        model_exists = None
        """ Generates a number that can help in making our reg no random thus unique """
        try:
            #random_number = model.objects.all().count()
            
            random_number = generate_random_number()
        
            reg_no = GetUniqueId(random_number).get_unique_id()
        
            model_exists = model.objects.filter(reg_no=reg_no).exists()
        
        except Exception as e:
            print('##############3')
            print(e)
            """ Incase there is an error in get the model just get the reg_no
                without checking its uniqueness because its hard for GetUniqueId
                to produce a non unique ID
            """
            reg_no = GetUniqueId(random_number).get_unique_id()
        
        if not model_exists:
            break
            
    return reg_no


