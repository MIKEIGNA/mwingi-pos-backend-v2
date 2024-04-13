import random

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings

from accounts.models import UserGroup


from core.time_utils.time_localizers import utc_to_local_datetime

from inventories.models import Supplier
from profiles.models import Profile, EmployeeProfile, Customer
from accounts.utils.user_type import EMPLOYEE_USER, TOP_USER

User = get_user_model()




# =========================== Top User =======================================

def initial_data_for_top_user_profile(user):

    # Save initial data for profile
    profile = Profile.objects.get(user=user)
    profile.business_name = 'Skypac'
    profile.location = 'Nairobi'
    profile.save()


def create_top_user_assets(
        first_name,
        last_name,
        phone,
        gender,
        created_date=utc_to_local_datetime(timezone.now())):
    
    email = '{}@gmail.com'.format(first_name.lower())

    if first_name == 'Angelina':
        email = settings.LOYVERSE_OWNER_EMAIL_ACCOUNT
    
    user = User.objects.create_user(
        email=email,
        first_name=first_name.title(),
        last_name=last_name,
        phone=phone,
        user_type=TOP_USER,
        gender=gender,
        password='secretpass',
    )

    

    initial_data_for_top_user_profile(user)

    return user


def create_new_user(user, created_date=utc_to_local_datetime(timezone.now())):

    if user == 'super':
        super_user = User.objects.create_superuser(
            email='john@gmail.com',
            first_name='John',
            last_name='Lock',
            phone='254710223322',
            gender=0,
            password='secretpass')

        initial_data_for_top_user_profile(super_user)

        return super_user
    
    elif user == 'angelina':

        created_user = create_top_user_assets(
            'Angelina',
            'Jolie',
            '254710023322',
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'john':

        created_user = create_top_user_assets(
            'John',
            'Lock',
            '254710223322',
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'jack':

        created_user = create_top_user_assets(
            'Jack',
            'Shephard',
            '254720223322',
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'merideth':
        created_user = create_top_user_assets(
            'Merideth',
            'Grey',
            '254713223344',
            gender=1,
            created_date=created_date)

        return created_user

    elif user == 'cristina':

        created_user = create_top_user_assets(
            'Cristina',
            'Yang',
            '254713223355',
            gender=1,
            created_date=created_date)

        return created_user

    elif user == 'izzie':

        created_user = create_top_user_assets(
            'Izzie',
            'Stevens',
            '254713223366',
            gender=1,
            created_date=created_date)

        return created_user

    elif user == 'george':

        created_user = create_top_user_assets(
            'George',
            'Omalley',
            '254713223377',
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'miranda':

        created_user = create_top_user_assets(
            'Miranda',
            'Bailey',
            '254713223388',
            gender=1,
            created_date=created_date)

        return created_user

    elif user == 'derek':

        created_user = create_top_user_assets(
            'Derek',
            'Shephard',
            '254713223399',
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'callie':

        created_user = create_top_user_assets(
            'Callie',
            'Torres',
            '254713223312',
            gender=1,
            created_date=created_date)

        return created_user

    elif user == 'mark':

        created_user = create_top_user_assets(
            'Mark',
            'Sloan',
            '254713223313',
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'owen':

        created_user = create_top_user_assets(
            'Owen',
            'Hunt',
            '254713223314',
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'arizona':

        created_user = create_top_user_assets(
            'Arizona',
            'Robbins',
            '254713223315',
            gender=1,
            created_date=created_date)

        return created_user

    elif user == 'walt':

        created_user = create_top_user_assets(
            'Walt',
            'Lloyd',
            '254713223316',
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'micheal':

        created_user = create_top_user_assets(
            'Micheal',
            'Dawson',
            '254713223317',
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'teddy':

        created_user = create_top_user_assets(
            'Tedy',
            'Altman',
            '254713223318',
            gender=1,
            created_date=created_date)

        return created_user


# =========================== Manager User =======================================


def create_manager_assets(
        first_name,
        last_name,
        phone,
        profile,
        store,
        gender,
        created_date=utc_to_local_datetime(timezone.now())
    ):

    manager_group = UserGroup.objects.get(
        master_user=profile.user, ident_name='Manager'
    )

    user = User.objects.create_user(
        email='{}@gmail.com'.format(first_name.lower()),
        first_name=first_name.title(),
        last_name=last_name,
        phone=phone,
        user_type=EMPLOYEE_USER,
        gender=gender,
        password='secretpass',
    )

    employee_profile = EmployeeProfile.objects.create(
        user=user,
        profile=profile,
        phone=user.phone,
        location='Upper Hill',
        join_date=created_date,
        role_reg_no=manager_group.reg_no
    )
    employee_profile.stores.add(store)



    

    return user


def create_new_manager_user(
        user,
        profile,
        store,
        created_date=utc_to_local_datetime(timezone.now())):

    if user == 'gucci':
        created_user = create_manager_assets(
            'Gucci',
            'Gucci',
            '254721223333',
            profile,
            store,
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'lewis':
        created_user = create_manager_assets(
            'Lewis',
            'Hamilton',
            '254721223344',
            profile,
            store,
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'cristiano':

        created_user = create_manager_assets(
            'Cristiano',
            'Ronaldo',
            '254721223366',
            profile,
            store,
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'lionel':

        created_user = create_manager_assets(
            'Lionel',
            'Messi',
            '254721223355',
            profile,
            store,
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'frank':

        created_user = create_manager_assets(
            'Frank',
            'Lampard',
            '254721223367',
            profile,
            store,
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'ashley':

        created_user = create_manager_assets(
            'Ashley',
            'Cole',
            '254721223368',
            profile,
            store,
            gender=1,
            created_date=created_date)

        return created_user

    elif user == 'neymar':

        created_user = create_manager_assets(
            'Neymar',
            'Junior',
            '254721223369',
            profile,
            store,
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'luiz':

        created_user = create_manager_assets(
            'Luiz',
            'Suarez',
            '254721223370',
            profile,
            store,
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'paul':

        created_user = create_manager_assets(
            'Paul',
            'Pogba',
            '254721223371',
            profile,
            store,
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'sergio':

        created_user = create_manager_assets(
            'Sergio',
            'Aguero',
            '254721223372',
            profile,
            store,
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'sadio':

        created_user = create_manager_assets(
            'Sadio',
            'Mane',
            '254721223373',
            profile,
            store,
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'kylian':

        created_user = create_manager_assets(
            'Kylian',
            'Mbape',
            '254721223374',
            profile,
            store,
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'wayne':

        created_user = create_manager_assets(
            'Wayne',
            'Rooney',
            '254721223375',
            profile,
            store,
            gender=0,
            created_date=created_date)

        return created_user


# =========================== Cashier User =======================================


def create_cashier_assets(
        first_name,
        last_name,
        phone,
        profile,
        store,
        gender,
        created_date=utc_to_local_datetime(timezone.now()),
        api_user=False,
    ):

    cashier_group = UserGroup.objects.get(
        master_user=profile.user, ident_name='Cashier'
    )

    user = User.objects.create_user(
        email='{}@gmail.com'.format(first_name.lower()),
        first_name=first_name.title(),
        last_name=last_name,
        phone=phone,
        user_type=EMPLOYEE_USER,
        gender=gender,
        password='secretpass',
    )

    employee_profile = EmployeeProfile.objects.create(
        user=user,
        profile=profile,
        phone=user.phone,
        location='Killimani',
        join_date=created_date,
        role_reg_no=cashier_group.reg_no,
        is_api_user=api_user
    )
    employee_profile.stores.add(store)

    return user


def create_new_cashier_user(
        user,
        profile,
        store,
        created_date=utc_to_local_datetime(timezone.now())):

    if user == 'ben':
        created_user = create_cashier_assets(
            'Ben',
            'Linus',
            '254711223344',
            profile,
            store,
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'james':

        created_user = create_cashier_assets(
            'James',
            'Sawer',
            '254711223355',
            profile,
            store,
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'kate':

        created_user = create_cashier_assets(
            'Kate',
            'Austen',
            '254711223366',
            profile,
            store,
            gender=1,
            created_date=created_date)

        return created_user

    elif user == 'hugo':

        created_user = create_cashier_assets(
            'Hugo',
            'Hurley',
            '254711223377',
            profile,
            store,
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'juliet':

        created_user = create_cashier_assets(
            'Juliet',
            'Burke',
            '254711223388',
            profile,
            store,
            gender=1,
            created_date=created_date)

        return created_user

    elif user == 'claire':

        created_user = create_cashier_assets(
            'Claire',
            'Littleton',
            '254711223399',
            profile,
            store,
            gender=1,
            created_date=created_date)

        return created_user

    elif user == 'charlie':

        created_user = create_cashier_assets(
            'Charlie',
            'Pace',
            '254711223312',
            profile,
            store,
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'sayid':

        created_user = create_cashier_assets(
            'Sayid',
            'Jarah',
            '254711223313',
            profile,
            store,
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'desmond':

        created_user = create_cashier_assets(
            'Desmond',
            'Hume',
            '254711223314',
            profile,
            store,
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'richard':

        created_user = create_cashier_assets(
            'Richard',
            'Alpart',
            '254711223315',
            profile,
            store,
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'walt':

        created_user = create_cashier_assets(
            'Walt',
            'Lloyd',
            '254711223316',
            profile,
            store,
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'micheal':

        created_user = create_cashier_assets(
            'Micheal',
            'Dawson',
            '254711223317',
            profile,
            store,
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'bernard':

        created_user = create_cashier_assets(
            'Bernard',
            'Nadler',
            '254711223318',
            profile,
            store,
            gender=0,
            created_date=created_date)

        return created_user

    elif user == 'ana':

        created_user = create_cashier_assets(
            'Ana',
            'Lucia',
            '254711223319',
            profile,
            store,
            gender=1,
            created_date=created_date)

    elif user == 'penny':

        created_user = create_cashier_assets(
            'Penny',
            'Widmore',
            '254711223320',
            profile,
            store,
            gender=1,
            created_date=created_date)

        return created_user


def create_new_customer(profile, name, created_date=utc_to_local_datetime(timezone.now())):

    if name == 'chris':
        customer = Customer.objects.create(
            profile=profile,
            name='Chris Evans',
            email='chris@gmail.com',
            village_name='Village',
            phone=254710101010,
            address='Donholm',
            city='Nairobi',
            region='Africa',
            postal_code='11011',
            country='Kenya',
            created_date=created_date
        )

        return customer

    elif name == 'alex':
        customer = Customer.objects.create(
            profile=profile,
            name='Alex Alexo',
            email='alex@gmail.com',
            village_name='Village',
            phone=254710102010,
            address='Donholm',
            city='Nairobi',
            region='Africa',
            postal_code='11011',
            country='Kenya',
            created_date=created_date
        )

        return customer

    elif name == 'dan':
        customer = Customer.objects.create(
            profile=profile,
            name='Dan Danko',
            email='danco@gmail.com',
            village_name='Village',
            phone=254710103010,
            address='Donholm',
            city='Nairobi',
            region='Africa',
            postal_code='11011',
            country='Kenya',
            created_date=created_date
        )

        return customer

    elif name == 'eric':
        customer = Customer.objects.create(
            profile=profile,
            name='Eric Erico',
            email='erico@gmail.com',
            village_name='Village',
            phone=254710107010,
            address='Donholm',
            city='Nairobi',
            region='Africa',
            postal_code='11011',
            country='Kenya',
            created_date=created_date
        )

        return customer

    elif name == 'kevin':
        customer = Customer.objects.create(
            profile=profile,
            name='Kevin Kevo',
            email='kevo@gmail.com',
            village_name='Village',
            phone=254710108010,
            address='Donholm',
            city='Nairobi',
            region='Africa',
            postal_code='11011',
            country='Kenya',
            created_date=created_date
        )

        return customer


def create_new_supplier(profile, name, created_date=utc_to_local_datetime(timezone.now())):

    if name == 'jeremy':
        suppplier = Supplier.objects.create(
            profile=profile,
            name='Jeremy Clackson',
            email=f'{name}@gmail.com',
            phone=254710104010,
            address='Donholm',
            city='Nairobi',
            region='Africa',
            postal_code='11011',
            country='Kenya',
            created_date=created_date
        )

        return suppplier

    elif name == 'james':
        suppplier = Supplier.objects.create(
            profile=profile,
            name='James May',
            email=f'{name}@gmail.com',
            phone=254710105010,
            address='Donholm',
            city='Nairobi',
            region='Africa',
            postal_code='11011',
            country='Kenya',
            created_date=created_date
        )

        return suppplier

    elif name == 'richard':
        suppplier = Supplier.objects.create(
            profile=profile,
            name='Richard Hammond',
            email=f'{name}@gmail.com',
            phone=254710106010,
            address='Donholm',
            city='Nairobi',
            region='Africa',
            postal_code='11011',
            country='Kenya',
            created_date=created_date
        )

        return suppplier


def create_new_random_customer_user(
        profile, count, created_date=utc_to_local_datetime(timezone.now())):

    user_names = []

    for i in range(count):

        user = profile.user

        customer_email = f'{(user.first_name).lower()}{i}@gmail.com'

        name = f'{user.first_name} Customer number{i}'

        Customer.objects.create(
            profile=profile,
            name=name,
            email=customer_email,
            phone=get_random_safcom_number(),
            address='Donholm',
            city='Nairobi',
            region='Africa',
            postal_code='11011',
            country='Kenya',
            created_date=created_date
        )

        user_names.append(name)

    return user_names




def create_new_random_supplier_user(
        profile, count, created_date=utc_to_local_datetime(timezone.now())):

    user_names = []

    for i in range(count):

        user = profile.user

        customer_email = f'{(user.first_name).lower()}{i}@gmail.com'

        name = f'{user.first_name} Supplier number{i}'

        Supplier.objects.create(
            profile=profile,
            name=name,
            email=customer_email,
            phone=get_random_safcom_number(),
            address='Donholm',
            city='Nairobi',
            region='Africa',
            postal_code='11011',
            country='Kenya',
            created_date=created_date
        )

        user_names.append(name)

    return user_names


def create_new_random_cashier_user(
        profile, store, count, created_date=utc_to_local_datetime(timezone.now())):

    user_names = []

    for i in range(count):

        first_name = f'firstname{i}'
        last_name = f'lastname{i}'

        create_cashier_assets(
            first_name,
            last_name,
            get_random_safcom_number(),
            profile,
            store,
            0,
            created_date
        )

        user_names.append(first_name)

    return user_names


def get_random_safcom_number():
    # Produces unique phones

    phone = '25470{}{}{}{}{}{}{} '.format(
        random.randint(0, 9),
        random.randint(0, 9),
        random.randint(0, 9),
        random.randint(0, 9),
        random.randint(0, 9),
        random.randint(0, 9),
        random.randint(0, 9))

    return phone
