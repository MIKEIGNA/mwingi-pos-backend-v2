from django.db.models.query_utils import Q
from django.shortcuts import get_object_or_404
from django.conf import settings 
from django.contrib.auth import get_user_model

from rest_framework import permissions
from rest_framework import generics
from rest_framework.exceptions import Throttled
from rest_framework.response import Response
from rest_framework import filters

from api.serializers.profiles.employee_profile_serializers import EpLeanUserProfileIndexViewSerializer
from api.utils.permission_helpers.api_view_permissions import IsEmployeeUserPermission
from api.utils.api_pagination import LeanResultsSetPagination
from core.image_utils import ApiImageUploader, ApiImageVerifier

from core.mixins.log_entry_mixin import UserActivityLogMixin
from core.my_throttle import ratelimit
from core.logging_utils import clean_logging_fields
from core.mixins.api_view_image_crop_mixin import ApiCropImageMixin

from profiles.models import EmployeeProfile
from api.serializers import (
    EmployeeProfileEditViewSerializer,
    EmployeeProfilePictureEditViewSerializer
)


IMAGE_SETTINGS = settings.IMAGE_SETTINGS
MEDIA_ROOT = settings.MEDIA_ROOT
User = get_user_model()
THROTTLE_RATES = settings.THROTTLE_RATES

 
class EmployeeProfileEditView(UserActivityLogMixin, generics.RetrieveUpdateAPIView):
    """ This view represents both the IndexView and CreateView for Profile """
    queryset = EmployeeProfile.objects.all()
    serializer_class = EmployeeProfileEditViewSerializer
    permission_classes = (permissions.IsAuthenticated,)
 
    def get_queryset(self):
        """
        Make sure only the owner can view his/her profile 
        """
        queryset = super(EmployeeProfileEditView, self).get_queryset()
        queryset = queryset.filter(user__email=self.request.user)
        
        return queryset
    
    def get_object(self):
        """ 
        For UX logger to work, the model should be stored in a variable
        named "self.obj" in the view instance
        """
        
        queryset = self.filter_queryset(self.get_queryset())
            
        # Get the single item from the filtered queryset
        self.obj = get_object_or_404(queryset)
                   
        # May raise a permission denied
        self.check_object_permissions(self.request, self.obj)
        
        """ Specify fields to log """
        self.ux_fields_to_log(['location', 'phone'])
            
        return self.obj
    
    def manually_log_errors(self, serializer):
        
        data = dict(serializer.data)
            
        """ This will remove sensitive info like passwords """
        data = clean_logging_fields(data)
            
            
        message = '"{}<=>{}{}<=>{}"'.format(
            'form_invalid', 
            dict(serializer.errors), 
            dict(serializer.errors), data)
            
        self.request._request.invalid_msg = message
        
    def update(self, request, *args, **kwargs):
        """
        By including an update() method here, we override the one in the
        UserActivityLogMixin. So we have to log our error from this view manually.
        
        We have overrided this method here because we wanted to add extra phone
        validation here (check if the phone is unique)
        """
        
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        """ If serializer is not valid, log the error """
        if not serializer.is_valid():
            self.manually_log_errors(serializer)
            
        """ If serializer is valid continue otherwise raise an exception """
        serializer.is_valid(raise_exception=True)
        
        # Call the super update()
        return super(EmployeeProfileEditView, self).update(request, *args, **kwargs)
        
    def perform_update(self, serializer):
        serializer.save()
        
        """ Log changed fields """  
        self.ux_log_changed_fields_api()
        

class EmployeeProfilePictureEditView(UserActivityLogMixin, ApiCropImageMixin, generics.UpdateAPIView):
    """ This view represents both the IndexView and CreateView for Profile """
    queryset = EmployeeProfile.objects.all()
    serializer_class = EmployeeProfilePictureEditViewSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        """ 
        For UX logger to work, the model should be stored in a variable
        named "self.obj" in the view instance
        """        
        queryset = self.filter_queryset(self.get_queryset())
            
        # Get the single item from the filtered queryset
        self.obj = get_object_or_404(queryset)
                   
        # May raise a permission denied
        self.check_object_permissions(self.request, self.obj)
        
        return self.obj
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her profile 
        """
     
        queryset = super(EmployeeProfilePictureEditView, self).get_queryset()
        queryset = queryset.filter(user__email=self.request.user)
        
        return queryset
    
    @ratelimit(
        scope='api_user', 
        rate=THROTTLE_RATES['api_profile_image_rate'], 
        alt_name='api_profile_image'
    )
    def put(self, request, *args, **kwargs):
        
        # if api_throttled is in kwargs, throttle the view 
        if kwargs.get('request_throttled', None):
            response = self.handle_exception(Throttled(1))
            self.response = self.finalize_response(request, response, *args, **kwargs)
            
            return self.response
    
        return self.update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
    
        serializer.is_valid(raise_exception=True)
                
        # ********** Do your stuff here

        #  Skip this op if new image has not been passed
        uploaded_image = serializer.validated_data.get('uploaded_image', None)
        if uploaded_image:

            # Verifies an image
            image_error_response = ApiImageVerifier.verify_image(uploaded_image)

            # Return image error if we have any
            if image_error_response: return image_error_response

    
        # ********** Do your stuff here

        #  Skip this op if new image has not been passed
        if uploaded_image:
            self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
            
        return Response(serializer.data)

    def perform_update(self, serializer):

        # We save image manually
        self.save_image(serializer)

    def save_image(self, serializer):
        
        # Save image if we have 1
        uploaded_image = serializer.validated_data.get('uploaded_image', None)

        if uploaded_image:
            ApiImageUploader(
                model = serializer.instance,
                serializer_image = uploaded_image
            ).save_and_upload()
    
     
class EpLeanUserIndexView(generics.ListAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = EpLeanUserProfileIndexViewSerializer
    permission_classes = (permissions.IsAuthenticated, IsEmployeeUserPermission)
    pagination_class = LeanResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name', 'last_name', 'email']

    def get_queryset(self):
        """
        Make sure only the owner can view his/her models
        """
        queryset = super(EpLeanUserIndexView, self).get_queryset()

        employee_profile = EmployeeProfile.objects.get(user=self.request.user)

        queryset = queryset.filter(
            Q(employeeprofile__stores__employeeprofile=employee_profile) | 
            Q(
                reg_no=self.request.user.employeeprofile.profile.reg_no,
                profile__store__employeeprofile=employee_profile
             )
        ).order_by('-id').distinct()

        return queryset