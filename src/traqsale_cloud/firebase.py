import os

import firebase_admin
from firebase_admin import credentials

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traqsale_cloud.settings')

cred = credentials.Certificate("./traqsale_cloud/firebase_settings/firebase.json")
app = firebase_admin.initialize_app(cred)