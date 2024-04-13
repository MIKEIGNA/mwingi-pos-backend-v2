from decimal import Decimal

from django.db.models.functions import Coalesce
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.aggregates import Sum
from django.utils import timezone
from django.contrib.sessions.models import Session
from django.contrib.auth.models import Group
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)
from django.contrib.auth.models import Group, Permission


from core.queryset_helpers import QuerysetFilterHelpers
from core.time_utils.time_localizers import utc_to_local_datetime_with_format
from core.token_generator import RandomStringTokenGenerator


from .utils.validators import validate_phone_for_models
from .utils.user_type import (
    EMPLOYEE_USER,
    USER_TYPE_CHOICES, 
    TOP_USER, 
    USER_GENDER_CHOICES
)

class UserManager(BaseUserManager):
    def create_user(
        self, 
        email, 
        first_name, 
        last_name, 
        phone, 
        user_type, 
        password=None, 
        **extra_fields):
        """
        Creates and saves a User with the given email, first name,
        last name and password.
        """
        if not email:
            raise ValueError("Users must have an email!")
        if not first_name:
            raise ValueError("Users must have a first name!")
        # if not last_name:
        #     raise ValueError("Users must have a last name!")
        # if not phone:
        #     raise ValueError("Users must have a phone phone!")
        
        
        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            user_type=user_type,
            **extra_fields,
        )
        
        user.set_password(password)
        user.save(using=self._db)
        
        return user

    def create_superuser(self, email, first_name, last_name, phone, password, **extra_fields):
        user = self.create_user(
                email, 
                first_name,
                last_name,
                phone,
                TOP_USER,
                password,
                **extra_fields
                )
        
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
            verbose_name='email',
            max_length=100,
            unique=True,
            )
    first_name = models.CharField(
            verbose_name='first name',
            max_length=100
            )
    last_name = models.CharField(
            verbose_name='last name',
            max_length=100,
            default='',
            blank=True,
            null=True
            )
    full_name = models.CharField(
            verbose_name='full name',
            max_length=150
            )
    phone = models.BigIntegerField(
            verbose_name='phone',
            # validators=[validate_phone_for_models,],
            # unique=True,
            default=0
            )# phone should only be editable through the profile model
    join_date = models.DateTimeField(
            verbose_name='join date',
            auto_now_add=True
            )
    is_active = models.BooleanField(
            verbose_name='is active',
            default=True
            )
    is_staff = models.BooleanField(
            verbose_name='is staff',
            default=False
            )
    user_type = models.IntegerField(
            verbose_name='user type',
            choices=USER_TYPE_CHOICES,
            )
    gender = models.IntegerField(
        verbose_name='gender',
        choices=USER_GENDER_CHOICES,
        default=0
    )
    reg_no = models.BigIntegerField(
            verbose_name='reg no',
            unique=True,
            default=0,
            editable=False
            )
    loyverse_employee_id = models.UUIDField(
        verbose_name='loyverse employee id',
        db_index=True,
        null=True,
        blank=True,
    )
    loyverse_store_id = models.UUIDField(
        verbose_name='loyverse store id',
        db_index=True,
        null=True,
        blank=True,
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "phone"]
    
    def __str__(self):
        return "{}".format(self.email)

    def get_short_name(self):
        return self.first_name
    
    def get_full_name(self):

        first_name = self.first_name
        last_name = self.last_name

        if self.last_name == 'Not available':
            last_name = ""

        return "{} {}".format(first_name, last_name)
    
    def get_join_date(self, local_timezone):
        """ Return the creation date in local time format """
        return utc_to_local_datetime_with_format(self.join_date, local_timezone)

    def get_user_timezone(self):
        """ Returns the timezone for the user """
        return settings.LOCATION_TIMEZONE
        
    def get_profile_image_url(self):
        """
        Return image url or an empty string
        """
    
        if self.user_type == TOP_USER:
            return self.profile.get_profile_image_url()

        elif self.user_type == EMPLOYEE_USER:
            return self.employeeprofile.get_profile_image_url()

        else:
            return ""

    def get_profile_reg_no(self):
        """
        Return reg_no or an empty string
        """
        return self.reg_no

    def get_report_data(
        self, 
        local_timezone,
        date_after=None, 
        date_before=None, 
        store_reg_nos=None):

        queryset = self.receipt_set.all()

        # Filters queryset with date range of the passed date field name
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset, 
            'created_date', 
            date_after, 
            date_before,
            local_timezone
        )

        if store_reg_nos:
            queryset = queryset.filter(store__reg_no__in=store_reg_nos)

        amount_aggregate = queryset.aggregate(
            discount=Coalesce(Sum('discount_amount'), Decimal(0.00)),
            gross_sales=Coalesce(Sum('total_amount'), Decimal(0.00)), 
            net_sales=Coalesce(Sum('subtotal_amount'), Decimal(0.00)),
        )

        refund_amount = queryset.filter(is_refund=True).aggregate(
            refund=Coalesce(Sum('total_amount'), Decimal(0.00)))['refund']

        return {
            'name': self.get_full_name(),
            'discount': str(round(amount_aggregate['discount'], 2)),
            'gross_sales': str(round(amount_aggregate['gross_sales'], 2)),
            'net_sales': str(round(amount_aggregate['net_sales'], 2)),
            'refund_amount': str(round(refund_amount, 2)),
            'receipts_count': queryset.count()
        }
    
    def clear_user_perms(self):

        print(self.is_superuser)

        # Get all permsions
        # perms = Permission.objects.all()

        # print(perms)

        # for perm in perms:
        #     self.user_permissions.remove(perm)

        # self.save()


        # print("****** User perms cleared")
        # print(self.get_all_permissions())
        # self.groups.clear()
        # self.user_permissions.clear()
        # self.save()

        # print("User perms cleared")

    def has_perm_for_profits(self):
        return self.has_perm('accounts.can_view_profits')
    
    def create_api_user(self):

        from profiles.models import EmployeeProfile

        cashier_group = UserGroup.objects.get(
            master_user=self, ident_name='Cashier'
        )

        first_name = 'API'
        last_name = 'User'

        user = User.objects.create_user(
            email='{}@gmail.com'.format(first_name.lower()),
            first_name=first_name.title(),
            last_name=last_name,
            phone=0,
            user_type=EMPLOYEE_USER,
            gender=0,
        )

        EmployeeProfile.objects.create(
            user=user,
            profile=self.profile,
            phone=user.phone,
            location='Killimani',
            role_reg_no=cashier_group.reg_no,
            is_api_user=True
        )
        # employee_profile.stores.add(store)


    
    def save(self, *args, **kwargs):

        self.full_name = self.get_full_name()
        
        """ If reg_no is 0 get a unique reg_no """
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel
            
            """ Get the model class """
            model = (self.__class__)
            
            self.reg_no = GetUniqueRegNoForModel(model)
            
        super(User, self).save(*args, **kwargs) # Call the "real" save() method.


#---------------- Start user group model --------------------------
class UserGroup(Group):
    master_user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
    )
    ident_name = models.CharField(
        verbose_name='ident name',
        max_length=50
    )
    is_owner_group = models.BooleanField(
        verbose_name='is owner group',
        default=False,
        editable=False
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,
        default=0,
        editable=False
    )

    def __str__(self):
        return str(self.ident_name)
    
    def get_all_perms(self):
        return list(self.permissions.all().values_list('codename', flat=True))

    def get_employee_count(self):
        return User.objects.filter(groups=self).count()

    def get_user_permissions_state(self):
        """
        Returns a dict with permissions codename as key and a boolean value 
        indicating if the group has the permission or not
        """

        from accounts.create_permissions import PERMISSION_DEFS

        perms = [
            p[0] for p in self.permissions.all().order_by('id').values_list('codename')
        ]

        state = {}
        for key, _value in PERMISSION_DEFS.items():
            state[key] = key in perms
            
        return state
    
    def update_perms(self):

        from accounts.create_permissions import GetPermission

        if self.ident_name == 'Owner':
            self.permissions.set(GetPermission().get_owner_permissions())

        elif self.ident_name == 'Manager':
            self.permissions.set(GetPermission().get_manager_permissions())

        elif self.ident_name == 'Cashier':
            self.permissions.set(GetPermission().get_cashier_permissions())
    
    def save(self, *args, **kwargs):
        
        """ If reg_no is 0 get a unique reg_no """
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel
            
            """ Get the model class """
            model = (self.__class__)
            
            self.reg_no = GetUniqueRegNoForModel(model)
            
        super(UserGroup, self).save(*args, **kwargs) 

    


#---------------- Start user group model --------------------------


#---------------- Start user session model --------------------------   
class UserSession(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    
    def __str__(self):
        return "{}".format(self.user.email)

#---------------- End user session model -------------------------- 
    
#---------------- Start user channel record model --------------------------
class UserChannelRecord(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    is_api = models.BooleanField(
            verbose_name='is api',
            default=False) 
    channel_name = models.CharField(
            verbose_name='channel name',
            max_length=100,
            )
        
    def __str__(self):
        return str(self.channel_name)

#---------------- End user channel record model --------------------------

#---------------- Start websocket ticket model --------------------------
class WebSocketTicket(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    reg_no = models.BigIntegerField(
            verbose_name='reg no',
            unique=True,
            default=0,
            editable=False
            )

    def __str__(self):
        return "{}".format(self.user.email)

    def save(self, *args, **kwargs):
        
        """ If reg_no is 0 get a unique reg_no """
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel
                
            """ Get the model class """
            model = (self.__class__)
            
            self.reg_no = GetUniqueRegNoForModel(model)
                
        super(WebSocketTicket, self).save(*args, **kwargs) # Call the "real" save() method.
    
#---------------- End websocket ticket model --------------------------


#---------------- Start reset password token utils --------------------------
class ResetPasswordToken(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    # Key field, though it is not the primary key of the model
    key = models.CharField(
        verbose_name='key',
        max_length=64,
        db_index=True,
        unique=True)
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now,)

    def generate_key(self):
        """ generates a pseudo random code using os.urandom and binascii.hexlify """
        return RandomStringTokenGenerator().generate_token()

    def __str__(self):
        return "Password reset token for user {user}".format(user=self.user)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(ResetPasswordToken, self).save(*args, **kwargs)


def clear_expired(expiry_time):
    """
    Remove all expired tokens
    :param expiry_time: Token expiration time
    """
    ResetPasswordToken.objects.filter(created_date__lte=expiry_time).delete()

#---------------- End reset password token utils --------------------------


  