# Since we have 3 different settings for our 3 envs, this will provide a 
# central place for common installed apps

# Application definition
INSTALLED_APPS = [
    'daphne',
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'mysettings.apps.MysettingsConfig',
    'accounts.apps.AccountsConfig',
    'profiles.apps.ProfilesConfig',
    'billing.apps.BillingConfig',
    'stores.apps.StoresConfig',
    'mylogentries.apps.MylogentriesConfig',
    'inventories.apps.InventoriesConfig',
    'products.apps.ProductsConfig',
    'sales.apps.SalesConfig',
    'firebase.apps.FirebaseConfig',
    'clusters.apps.ClustersConfig',
    'loyverse.apps.LoyverseConfig',
    
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',

    'api.apps.ApiConfig',
    
    'channels',
    #'hijack',

    #'corsheaders',
    'django_celery_beat',
    # 'silk' # silk
]