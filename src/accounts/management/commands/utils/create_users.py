from django.contrib.auth import get_user_model

from profiles.models import Profile
from core.test_utils.create_user import create_new_user

User = get_user_model()

def create_user(first_name):
    
    email='{}@gmail.com'.format(first_name.lower())
    
    profile_exists = Profile.objects.filter(user__email=email).exists()
    
    if not profile_exists:
        
        print("Creating user {}".format(email))
        
        create_new_user(first_name)
        
    else:
        
        print("We already have user {}".format(email))
        



def create_users(delete_models):

    if delete_models:
        Profile.objects.all().delete()
    
    create_user("jack")
    
    create_user("john")
        

    
    
        
        

         
    