import os
import sys

# settings.py

import locale

# Set the collation order for string comparison to 'C' locale
locale.setlocale(locale.LC_COLLATE, 'C')

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MIDDLEWARE = [
    # 'silk.middleware.SilkyMiddleware', # silk
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.BrokenLinkEmailsMiddleware',
    'django.middleware.common.CommonMiddleware',
    
    'core.middlewares.logging_middleware.AuditLoggingMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ORIGIN_ALLOW_ALL = True

ROOT_URLCONF = 'traqsale_cloud.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'), ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'traqsale_cloud.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = False
USE_L10N = True
USE_TZ = True

# User settings
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
AUTH_USER_MODEL = 'accounts.User'
ADMIN_USER_URL = 'magnupe/'

TESTING_MODE = sys.argv[1:2] == ['test']


DEFAULT_START_DATE = '1972-01-01T00:00:00.000Z'

# ---------------- Logging Settings --------------------------------------

page_views_logger_settings = {
    'handlers': ['page_views_logfile'],
    'level': 'INFO',
    'propagate': True,
}

test_page_views_logger_settings = {
    'handlers': ['test_page_views_logfile'],
    'level': 'INFO',
    'propagate': True,
}

page_critical_logger_settings = {
    'handlers': ['page_critical_logfile'],
    'level': 'ERROR',
    'propagate': True,
}

test_page_critical_logger_settings = {
    'handlers': ['page_critical_logfile'],
    'level': 'ERROR',
    'propagate': True,
}

software_task_critical_logger_settings = {
    'handlers': ['software_task_critical_logfile'],
    'level': 'ERROR',
    'propagate': True,
}

test_software_task_critical_logger_settings = {
    'handlers': ['test_software_task_critical_logfile'],
    'level': 'ERROR',
    'propagate': True,
}

test_firebase_sender_logger_settings = {
    'handlers': ['test_firebase_sender_logfile'],
    'level': 'INFO',
    'propagate': True,
}


console_logger_settings = {
    'handlers': ['console'],
    'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'page_views_logfile': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': './xlogs/page_views.log',
            'formatter': 'simple'
        },
        'test_page_views_logfile': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': './xlogs/test_page_views.log',
            'formatter': 'simple'
        },
        'page_critical_logfile': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': './xlogs/page_critical.log',
            'formatter': 'simple'
        },
        'test_page_critical_logfile': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': './xlogs/test_page_critical.log',
            'formatter': 'simple'
        },

        'software_task_critical_logfile': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': './xlogs/software_task_critical.log',
            'formatter': 'simple'
        },
        'test_software_task_critical_logfile': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': './xlogs/test_software_task_critical.log',
            'formatter': 'simple'
        },

        'test_firebase_sender_logfile': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': './xlogs/test_firebase_sender.log',
            'formatter': 'simple'
        },


        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'page_views_logger': page_views_logger_settings,
        'page_critical_logger': page_critical_logger_settings,
        'test_page_views_logger': test_page_views_logger_settings,

        'software_task_critical_logger': software_task_critical_logger_settings,
        'test_software_task_critical_logger': test_software_task_critical_logger_settings,

        'test_firebase_sender_logger': test_firebase_sender_logger_settings,
    }
}

# Enable console logging when we are not testing
MQ_CONSOLE_LOGGING = False
if MQ_CONSOLE_LOGGING:
    console_logging = {
        'django': console_logger_settings,
        'celery': console_logger_settings,
    }

    LOGGING['loggers'].update(console_logging)

# ---------------- End Logging Settings -----------------------------------


# ---------------- Cache Settings --------------------------------------
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'my_cache_table',
    }
}
# ---------------- End Cache Settings --------------------------------------

""" ****************** Python Start ****************** """

PYTHON_REQUESTS_TIMEOUT = 120 # 2 Minutes

""" ****************** Python End ****************** """

""" ****************** Loyverse Start ****************** """
LOYVERSE_OWNER_EMAIL_ACCOUNT = os.environ.get("LOYVERSE_OWNER_EMAIL")
LOYVERSE_AUTH_URL = 'https://api.loyverse.com/oauth/token'
LOYVERSE_INVENTORY_URL = 'https://api.loyverse.com/v1.0/inventory?limit=250'
LOYVERSE_CUSTOMER_URL = 'https://api.loyverse.com/v1.0/customers?limit=250'
LOYVERSE_EMPLOYEE_URL = 'https://api.loyverse.com/v1.0/employees?limit=250'
LOYVERSE_TAXES_URL = 'https://api.loyverse.com/v1.0/taxes?limit=250'
LOYVERSE_CATEGORIES_URL = 'https://api.loyverse.com/v1.0/categories?limit=250'
LOYVERSE_STORES_URL = 'https://api.loyverse.com/v1.0/stores?limit=250'
LOYVERSE_ITEMS_URL = 'https://api.loyverse.com/v1.0/items?limit=250'
LOYVERSE_RECEIPTS_URL = 'https://api.loyverse.com/v1.0/receipts?limit=250'
LOYVERSE_RETDIRECT_URI = 'https://mwingi.traqsale.com/loyverse/thank-you'
LOYVERSE_RECEIPT_VIEW_URL = 'https://api.loyverse.com/v1.0/receipts/'
 
""" ****************** Loyverse End ****************** """

""" ****************** Payment Start ****************** """
BANK_NAME = "Equity Bank Ltd"
BANK_BRANCH_NAME = "Kimathi Street"
BANK_ACCOUNT_NUMBER = 999
BANK_ACCOUNT_NAME = "traqsale_cloud"


""" ****************** Payment End ****************** """

""" ****************** Mpesa Start ****************** """

MPESA_BUSINESS_SHORTCODE = 600134

SAFCOM_VALIDATION_ACCEPTED = {"ResultCode": 0,
                              "ResultDesc": "Accepted"
                              }

SAFCOM_VALIDATION_REJECTED = {"ResultCode": 1,
                              "ResultDesc": "Rejected"
                              }

SAFCOM_CONFIRMATION_SUCCESS = {"C2BPaymentConfirmationResult": "Success"}

SAFCOM_CONFIRMATION_FAILURE = {"C2BPaymentConfirmationResult": "Failure"}

MPESA_VALIDATION_RELATIVE_URL_PATH = "mpesa/validation"
MPESA_CONFIRMATION_RELATIVE_URL_PATH = "mpesa/confirmation"

MAX_MPESA_TRANSACTION = 300000

""" ********************************* Mpesa End ************************************ """


""" ********************************* My Throttle Start ********************************* """
# TODO For testing reasons, we increase throttle limits but we should change them
# befor going live
THROTTLE_RATES = {
    'login_rate': '10/m',
    'signup_rate': '6/m',
    'password_reset_rate': '6/m',
    'contact_rate': '8/m',

    'location_update_rate': '20/3m',
    'team_create_rate': '11/m',
    # For test compatibility issue, the rate should be divisible by 4 and 3
    'tracker_location_rate': '12/3m',

    'api_token_rate': '10/m',
    'api_employee_create_rate': '10/m',
    'api_tracker_location_rate': '12/3m',

    'change_phone_rate': '1/m',
    'change_phone_pass_key_rate': '1/m',


    'api_phone_connect_rate': '5/m',
    'api_change_phone_rate': '1/m',
    'api_change_phone_pass_key_rate': '1/m',

    'report_rate': '5/m',
    'api_report_rate': '5/m',

    'notification_rate': '10/m',
    'api_notification_rate': '10/m',

    'message_rate': '10/m',
    'api_message_rate': '10/m',

    'api_checkin_out_rate': '10/m',

    'profile_image_rate': '10/m',
    'api_profile_image_rate': '10/m',
    'api_receipt_image_rate': '10/m',

    'visit_location_rate': '12/3m',
    'api_visit_location_rate': '8/3m',

    'product_rate': '10/m',
    'api_product_rate': '10/m',
    'api_product_edit_rate': '10/m',
    'api_product_image_rate': '10/m',

    'api_modifier_rate': '10/m',

    'customer_rate': '10/m',
    'api_customer_rate': '10/m',

    'invoice_rate': '10/m',
    'api_invoice_rate': '10/m',

    'store_rate': '10/m',
    'api_store_rate': '10/m',

    'tax_rate': '10/m',
    'api_tax_rate': '10/m',

    'api_discount_rate': '10/m',

    'api_category_rate': '10/m',
    'api_receipt_rate': '10/m',
    'api_supplier_rate': '10/m',
    'api_10_per_minute_create_rate': '10/m',
    'api_transfer_order_rate': '10/m',
    'api_inventory_count_rate': '10/m',
    'api_purchase_order_rate': '10/m',
    'api_10_per_minute_create_rate': '10/m'
}

""" **************************************** My Throttle End **************************************** """


DEFAULT_STORE_NAME = 'HQ Store'

""" **************************************** Timezone  Start **************************************** """
LOCATION_TIMEZONE = 'Africa/Nairobi'
PREFERED_DATE_FORMAT = "%B, %d, %Y, %I:%M:%p"
PREFERED_DATE_FORMAT2 = "%b, %d, %Y, %I:%M:%p"
""" **************************************** Timezone End **************************************** """


""" **************************************** Prices  Start **************************************** """
SUBSCRIPTION_PRICES = {'account': 1500}

SUBSCRIPTION_PRICE_DISCOUNTS = {
    '1_months': 5,
    '3_months': 10,
    '6_months': 25,
    '12_months': 40
}

""" **************************************** Prices End **************************************** """

""" **************************************** General settings Start **************************************** """

MAX_MODIFIER_DESCRIPTION_LIMIT = 38

""" **************************************** General settings End **************************************** """

""" **************************************** Formsets  Start **************************************** """
MAX_STORE_PER_ACCOUNT = 1000
MAX_STORES_REG_MAX_LENGTH = MAX_STORE_PER_ACCOUNT * 15  # 1500
MAX_MODIFIER_COUNT = 10
MAX_PRODUCT_BUNDLE_COUNT = 10
MAX_RECEIPT_LINE_COUNT = 200
MAX_INVOICE_RECEIPT_COUNT = 200
MAX_STOCK_ADJUSTMENT_LINE_COUNT = 500
MAX_VARIANT_COUNT = 10
MAX_MODIFIER_OPTION_COUNT = 20
""" **************************************** Formsets End **************************************** """


""" **************************************** Pagination  Start **************************************** """
LEAN_PAGINATION_PAGE_SIZE = 200




PRODUCT_POS_PAGINATION_PAGE_SIZE = 20

INVENTORY_VALUATION_PAGINATION_PAGE_SIZE = 120
REPORT_PAGINATION_PAGE_SIZE = 20

PRODUCT_LEAN_WEB_PAGINATION_PAGE_SIZE = 200
PRODUCT_WEB_PAGINATION_PAGE_SIZE = 200



MODIFIER_WEB_PAGINATION_PAGE_SIZE = 10
STANDARD_WEB_RESULTS_AND_STORES_PAGINATION = 10
INVENTORY_HISTORY_PAGINATION = 100


""" **************************************** Pagination End **************************************** """


""" **************************************** Notification  Start **************************************** """
NOTIFICATION_SETTINGS = {'notification_limit': 30, }
""" **************************************** Notification End **************************************** """

""" **************************************** Images Start **************************************** """
IMAGE_SETTINGS = {
    'no_image_url': 'images/no_image.jpg',
    'profile_images_dir': 'images/profiles/',
    'product_images_dir': 'images/products/',
    'receipt_images_dir': 'images/receipts/'

}
DEFAULT_COLOR_CODE = '#474A49'

""" **************************************** Images End **************************************** """


""" ******************** Celery Custom Settings Start ******************** """
# Custom settings
DO_TASK_IN_CELERY_BACKGROUND = True
CELERY_MIDNIGHT_PERIODIC_TASK_NAME = "midnight_task"

CELERY_CREATE_STORE_TASK_NAME = "create_stores_task"
CELERY_CREATE_STAFF_TASK_NAME = "create_staff_task"
CELERY_CREATE_CUSTOMER_TASK_NAME = "create_customer_task"
CELERY_CREATE_TAX_TASK_NAME = "create_tax_task"
CELERY_CREATE_CLOSED_CASH_TASK_NAME = "create_closed_cash_task"


CELERY_CREATE_CATEGORY_TASK_NAME = "create_categories_task"
CELERY_CREATE_PRODUCT_TASK_NAME = "create_products_task"
CELERY_CREATE_TICKET_TASK_NAME = "create_tickets_task"
""" ******************** Celery Custom Settings End ******************** """


""" ******************** Global Email Settings Start ******************** """
EMAIL_ERROR_REPORTING_ADDRESS = 'dollaurgent@gmail.com'
EMAIL_HEADERS = {'From': 'traqsale_cloud <info@traqsale_cloud.com>'}
""" ******************** Global Email Settings End ******************** """

WE_IN_CLOUD = int(os.environ.get("WE_IN_CLOUD", default=0))


""" **************** Mwingi Connector  Start **************** """
MWINGI_CONN_BASE_URL = 'https://mwingiconnector.traqsale.com'
MWINGI_CONN_RECEIPTS_URL =f'{MWINGI_CONN_BASE_URL}/api/loyverse/webhook/receipt-update/'
MWINGI_CONN_CUSTOMER_URL =f'{MWINGI_CONN_BASE_URL}/api/loyverse/customer-update/'
MWINGI_CONN_INVENTORY_URL =f'{MWINGI_CONN_BASE_URL}/api/loyverse/inventory-update/'
""" **************** Mwingi Connector End **************** """


""" **************** Mwingi Old Connector  Start **************** """
MWINGI_OLD_CONN_BASE_URL = 'https://mwingi.traqsale.com'
MWINGI_OLD_CONN_INVENTORY_URL =f'{MWINGI_OLD_CONN_BASE_URL}/api/pos/inventory-update/'
""" **************** Mwingi Old Connector End **************** """

# ---------------- REST password Settings --------------------------------------

DJANGO_REST_MULTITOKENAUTH_RESET_TOKEN_EXPIRY_TIME = 24

if WE_IN_CLOUD:
    FRONTEND_SITE_NAME = 'https://backoffice.traqsale_cloud.com/'
else:
    FRONTEND_SITE_NAME = 'http://localhost:4200'

# ---------------- End REST password Settings --------------------------------------
