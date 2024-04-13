
import os
import sys

from core.db_utils import DbUtils

# pylint: disable=wildcard-import
TESTING_MODE = sys.argv[1:2] == ['test']
WE_IN_CLOUD = int(os.environ.get("WE_IN_CLOUD", default=0))
WE_IN_DOCKER = int(os.environ.get("WE_IN_DOCKER", default=0))

#---------------- Main Settings ---------------------------------------
if WE_IN_CLOUD:
    print("We are in the cloud")
    from .settings_in_aws import *
else:
    if WE_IN_DOCKER:
        print("We are in a docker container")
        from .settings_in_docker import *
    else:
        print("We are in a local machine")
        from .settings_in_dev import *

#---------------- Local Settings ---------------------------------------
from .app_settings import *

if not DEBUG: # pylint: disable=used-before-assignment

    if DbUtils.check_if_we_are_in_production():
        MY_SITE_URL = 'https://portal.traqsale.com'
    else:
        MY_SITE_URL = 'https://mwingi-pos-staging.traqsale.com'
else:
    MY_SITE_URL = 'http://127.0.0.1:8000' 

# Imports development or production settings depending on the debug value
if DEBUG: # pylint: disable=used-before-assignment
    print("We are in degug mode")
    from .local_settings.development import * 
else:
    print("We are in production mode")
    from .local_settings.production import *

    # Sentry logging
    if WE_IN_CLOUD and not TESTING_MODE:
        print("We are using sentry")
        from .local_settings.sentry import * 
#---------------- End Local Settings ----------------------------------- 
