import os
from django.contrib.auth import get_user_model
from accounts.utils.user_type import EMPLOYEE_USER

from profiles.models import Profile, EmployeeProfile
from core.test_utils.create_user import create_new_cashier_user
from stores.models import Store


User = get_user_model()




def create_first_4_cashiers_users(profile):

    store1 = Store.objects.filter(profile=profile).order_by('id').first()
    
    # Create cashier 1
    try:
        EmployeeProfile.objects.get(user__email="james@gmail.com")
    except:
        create_new_cashier_user("james", profile, store1)
            
    # Create cashier 2
    try:
        EmployeeProfile.objects.get(user__email="kate@gmail.com")
    except:
        create_new_cashier_user("kate", profile, store1)
        
    # Create cashier 3
    try:
        EmployeeProfile.objects.get(user__email="ben@gmail.com")
    except:
        create_new_cashier_user("ben", profile, store1)
            
            
    # Create cashier 4
    try:
        EmployeeProfile.objects.get(user__email="hugo@gmail.com")
    except:
        create_new_cashier_user("hugo", profile, store1)



def create_cashier_users_for_top_user2():
    
    email = 'jack@gmail.com'
    profile = Profile.objects.get(user__email=email)
    
    store = Store.objects.filter(profile=profile).order_by('id').first()
    
    # Create superviosor 1
    try:
        EmployeeProfile.objects.get(user__email="juliet@gmail.com")
    except:
        create_new_cashier_user("juliet", profile, store)

    
    
def create_cashier_users(delete_models, count=30):

    if delete_models:
        EmployeeProfile.objects.filter(user__user_type=EMPLOYEE_USER).delete()
        

  
    try:
        email = os.environ.get("FIRST_USER_EMAIL")
        profile = Profile.objects.get(user__email=email)
        
        create_first_4_cashiers_users(profile)
        
        create_cashier_users_for_top_user2()
    except Exception as e:
        print(f"Error {e}")
        
        

         
    