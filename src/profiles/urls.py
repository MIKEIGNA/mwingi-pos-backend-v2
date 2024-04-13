from django.urls import path
from django.contrib.auth.decorators import login_required

from profiles.views import (

    ################ Top User ######################
    # Top user profile views
    ProfileView,
    EditProfileView,
    EditProfilePictureView,
)

app_name = 'profiles'
urlpatterns = [

    ################ Top User ######################
    # Top user profile views

    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', EditProfileView.as_view(), name='edit_profile'),
    path('profile/picture/edit/', EditProfilePictureView.as_view(),
         name='edit_profile_image'),
]
