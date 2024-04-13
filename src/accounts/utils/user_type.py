ADMIN_USER = 200000000 # Thsi will make it harder for an attacker to guess
TOP_USER = 1
EMPLOYEE_USER = 2

USER_TYPE_CHOICES =[
    (ADMIN_USER, 'admin',),
    (TOP_USER, 'Owner',),   
    (EMPLOYEE_USER, 'Employee',),
]

USER_GENDER_CHOICES =[
    (0, 'Male',),
    (1, 'Female',), 
    (2, 'Other',),  
]