
from pprint import pprint
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.contrib.auth.signals import user_logged_out

from rest_framework.authtoken.models import Token

from accounts.create_permissions import GetPermission
from core.image_utils import ModelImageHelpers
from loyverse.models import LoyverseAppData
from profiles.models import EmployeeProfile, Profile

from .utils.user_type import TOP_USER
from .models import UserSession, UserGroup
from .create_permissions import CreatePermission



@receiver(post_save, sender=get_user_model())
def create_top_user_addittional_models_signal(sender, instance, created, **kwargs):
    """
    Creates Profile, Token, MySetting and 3 UserGroup models (Owner, Manager, 
    Cashier)"""
    
    """ Profile and MySetting are imported here to prevent cyclic imports errors """
    from profiles.models import Profile
    from mysettings.models import MySetting
    
    if created: 
        
        # Create Token
        Token.objects.create(user=instance)  
        
        # Create Profile
        if instance.user_type == TOP_USER:
            
            profile = Profile.objects.get_or_create(
                user=instance,
                phone=instance.phone,
                reg_no=instance.reg_no
            ) # Create Profile

        else:
            """ 
            We are not creating EmployeeProfile here since they need the 
            Profile of the logged in user and we obviously cant get it from here
            """
            
        # Create MySetting
        ms = MySetting.objects.all().count() 
        
        if not ms:
            MySetting.objects.get_or_create(name='main')
            
            # Creates additional user permissions
            CreatePermission.create_permissions()


        # Create UserGroups
        if instance.user_type == TOP_USER:
            # Create owner user group and assign it to the current user instance
            owner_group = UserGroup.objects.create(
                master_user=instance, 
                name=f'Owner {instance.reg_no}',
                ident_name='Owner',
                is_owner_group=True
            )
            
            owner_group.permissions.set(GetPermission().get_owner_permissions())
            instance.groups.add(owner_group)

            # Create manager user group and it's permissions
            manager_group = UserGroup.objects.create(
                master_user=instance, 
                name=f'Manager {instance.reg_no}',
                ident_name='Manager',
            )
            manager_group.permissions.set(GetPermission().get_manager_permissions())

            # Create cashier user group and it's permissions
            cashier_group = UserGroup.objects.create(
                master_user=instance, 
                name=f'Cashier {instance.reg_no}',
                ident_name='Cashier',
            )
            cashier_group.permissions.set(GetPermission().get_cashier_permissions())

        # Create Loyverse auth if it does not exist
        LoyverseAppData.objects.get_or_create(name='main')



@receiver(post_save, sender=Session)
def session_created_signal(sender, instance, created, **kwargs):
    
    if created:
        
        session_user_id = instance.get_decoded().get('_auth_user_id')
        
        if session_user_id:
            user = get_user_model().objects.get(pk=session_user_id)
            session_id = instance.session_key
            
            UserSession.objects.get_or_create(
                    user = user,
                    session_id = session_id)



@receiver(post_delete, sender=get_user_model())
def user_delete_signal(sender, instance, **kwargs):
    """ 
    Update customer current debt
    """

    if instance.user_type == TOP_USER:
        Profile.objects.filter(user=instance).delete()
    else:
        EmployeeProfile.objects.filter(user=instance).delete()
 


# User logout signal
def user_logged_out_handler(sender, request, user, **kwargs):
    from .utils.logout_users import logout_user_everywhere
    logout_user_everywhere(user)
    
user_logged_out.connect(user_logged_out_handler)        
   