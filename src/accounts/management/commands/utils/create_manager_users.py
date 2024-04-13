import os
from django.contrib.auth import get_user_model
from accounts.utils.user_type import EMPLOYEE_USER

from profiles.models import Profile, EmployeeProfile
from core.test_utils.create_user import create_new_manager_user
from stores.models import Store


User = get_user_model()


# pylint: disable=bare-except

def create_first_4_managers_users(profile):

    store1 = Store.objects.filter(profile=profile).order_by('id').first()
    
    # Create manager 1
    try:
        EmployeeProfile.objects.get(user__email="gucci@gmail.com")
    except:
        create_new_manager_user("gucci", profile, store1)
            
    # Create manager 2
    try:
        EmployeeProfile.objects.get(user__email="lewis@gmail.com")
    except:
        create_new_manager_user("lewis", profile, store1)
        
    # Create manager 3
    try:
        EmployeeProfile.objects.get(user__email="cristiano@gmail.com")
    except:
        create_new_manager_user("cristiano", profile, store1)
            
            
    # Create manager 4
    try:
        EmployeeProfile.objects.get(user__email="lionel@gmail.com")
    except:
        create_new_manager_user("lionel", profile, store1)



def create_manager_users_for_top_user2():
    
    email = 'jack@gmail.com'
    profile = Profile.objects.get(user__email=email)
    
    store = Store.objects.filter(profile=profile).order_by('id').first()
    
    # Create superviosor 1
    try:
        EmployeeProfile.objects.get(user__email="frank@gmail.com")
    except:
        create_new_manager_user("frank", profile, store)

    
    
def create_manager_users(delete_models, count=30):

    if delete_models:
        EmployeeProfile.objects.filter(user__user_type=EMPLOYEE_USER).delete()
        

  
    try:
        email = os.environ.get("FIRST_USER_EMAIL")
        profile = Profile.objects.get(user__email=email)
        
        create_first_4_managers_users(profile)
        
        create_manager_users_for_top_user2()
    except Exception as e:
        print(f"Error {e}")
        
        

         
    