import django_filters.rest_framework
from django_filters.rest_framework import DjangoFilterBackend

from django.conf import settings 
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.http import Http404

from rest_framework import filters
from rest_framework import permissions
from rest_framework import generics
from rest_framework.exceptions import Throttled
from rest_framework.response import Response
from rest_framework import status
from accounts.models import UserGroup
from api.serializers.profiles.tp_employee_serializers import (
    TpEmployeeClusterViewSerializer, 
    TpEmployeeProfileClusterListSerializer
)
from api.utils.api_web_pagination import EmployeeWebResultsSetPagination, StandardWebResultsAndStoresSetPagination
from api.utils.permission_helpers.api_view_permissions import CanViewEmployeesPermission, IsTopUserPermission

from core.mixins.log_entry_mixin import UserActivityLogMixin
from core.my_throttle import ratelimit
from core.my_settings import MySettingClass

from accounts.utils.user_type import EMPLOYEE_USER, TOP_USER

from profiles.models import Profile, EmployeeProfile

from api.utils.api_pagination import LeanResultsSetPagination, StandardResultsSetPagination_10
from api.utils.api_view_formset_utils import ApiStoreFormestHelpers, ApiWebStoreFormestHelpers
from api.serializers import (
    TpLeanEmployeeProfileIndexViewSerializer,
    TpEmployeeProfileIndexViewSerializer,
    TpEmployeeProfileEditViewSerializer,
)
from stores.models import Store

class TpLeanEmployeeProfileIndexView(generics.ListAPIView):
    queryset = EmployeeProfile.objects.all().select_related('user')
    serializer_class = TpLeanEmployeeProfileIndexViewSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LeanResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__first_name', 'user__last_name', 'user__email']

    def get(self, request, *args, **kwargs):
        
        if not self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)
  
        return super(TpLeanEmployeeProfileIndexView, self).get(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her employee
        """
        queryset = super(TpLeanEmployeeProfileIndexView, self).get_queryset()

        queryset = queryset.filter(
            profile__user__email=self.request.user
        ).order_by('-id')

        return queryset

class TpEmployeeProfileIndexView(UserActivityLogMixin, generics.ListCreateAPIView):
    queryset = EmployeeProfile.objects.all().select_related('profile', 'user')
    serializer_class = TpEmployeeProfileIndexViewSerializer
    permission_classes = (
        permissions.IsAuthenticated, 
        IsTopUserPermission,
        CanViewEmployeesPermission
    )
    pagination_class = EmployeeWebResultsSetPagination
    filter_backends = [
        filters.SearchFilter, 
        django_filters.rest_framework.DjangoFilterBackend
    ]
    filterset_fields = ['stores__reg_no']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    
    # Custom fields
    collected_stores = []
    top_profile = None
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her employee
        """
        queryset = super(TpEmployeeProfileIndexView, self).get_queryset()

        queryset = queryset.filter(
            profile__user__email=self.request.user
        )

        queryset = queryset.order_by('user__first_name')

        return queryset
             
    @ratelimit(
        scope='api_ip', 
        rate=settings.THROTTLE_RATES['api_employee_create_rate'], 
        alt_name='api_employee_create'
    )
    def post(self, request, *args, **kwargs):
        
        # if api_throttled is in kwargs, throttle the view 
        if kwargs.get('request_throttled', None):
            response = self.handle_exception(Throttled(1))
            self.response = self.finalize_response(request, response, *args, **kwargs)
            
            return self.response
        
        allow_employee = MySettingClass.allow_new_employee()

        if not allow_employee:
            return Response(status=status.HTTP_423_LOCKED)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():

            self.top_profile = Profile.objects.get(user__email=self.request.user)

            """ Confirm if store belongs to the top user"""
            stores_info = serializer.validated_data['stores_info']

            self.collected_stores = ApiStoreFormestHelpers.validate_store_reg_nos_for_top_user(
                stores_info, self.top_profile
            )

            if not type(self.collected_stores) == list:
                error_data = {'stores_info': "You provided wrong stores."}
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST)

            
            # To avoid atomic block error, we verify user group here instead of
            # doint it in the serializer
            group_exists = UserGroup.objects.filter(
                master_user=self.request.user,
                reg_no=serializer.validated_data['role_reg_no'],
                is_owner_group=False
            ).exists()

            if not group_exists:
                error_data = {'role_reg_no': ["Wrong role was selected"]}
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST)
            
        return self.create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        
        try:
            self.create_employee_profile(serializer)
        except: # pylint: disable=bare-except
            "Log here"

    def create_employee_profile(self, serializer):
                
        first_name = serializer.validated_data['first_name']
        last_name = serializer.validated_data['last_name']
        email = serializer.validated_data['email']
        phone = serializer.validated_data['phone']
        role_reg_no = serializer.validated_data['role_reg_no']
        gender = serializer.validated_data['gender']   
        
        """ Create employee user """
        user = get_user_model().objects.create_user(
            first_name=first_name, 
            last_name=last_name, 
            email=email, 
            phone=phone,
            user_type = EMPLOYEE_USER,
            gender=gender,
        )

        user = get_user_model().objects.get(email=email)
        user.set_password('123456')
        user.save()
        
        employee_profile = EmployeeProfile.objects.create(
            user=user,
            profile=self.top_profile,
            phone=phone,
            reg_no=user.reg_no,
            role_reg_no=role_reg_no
        )
        employee_profile.stores.add(*self.collected_stores)

        
        #self.reg_no = employee_profile.reg_no
            
        """
        This is enclosed in a try statement coz it doesent work in 
        MagicMock's patch in testing
        """
        try:
            """ Log that new employee has been created """
            my_obj = employee_profile
            include_value = employee_profile.user.email  # Value to be included in the change message
                
            """ Log that a new object was created """ 
            self.ux_log_new_object_api(my_obj, include_value)
        except: # pylint: disable=bare-except
            "Log here"
        
    


class TpEmployeeProfileEditView(generics.RetrieveUpdateDestroyAPIView):
    queryset = EmployeeProfile.objects.all().select_related('user')
    serializer_class = TpEmployeeProfileEditViewSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanViewEmployeesPermission
    )
    lookup_field = 'reg_no'

    # Custom fields
    collected_stores = []
    top_profile = None
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her employee_profile
        """
        queryset = super(TpEmployeeProfileEditView, self).get_queryset()
        queryset = queryset.filter(profile__user__email=self.request.user, reg_no=self.kwargs['reg_no'])

        return queryset

    def get_object(self):
        
        queryset = self.filter_queryset(self.get_queryset())
            
        # Get the single item from the filtered queryset
        self.object = get_object_or_404(queryset)
                   
        # May raise a permission denied
        self.check_object_permissions(self.request, self.object)
            
        return self.object

    def get_store_list(self, queryset):
        """
        Returns a list with dicts that have store names and reg_nos
        """
        queryset = queryset.order_by('id')
        stores = [{'name': s.name, 'reg_no': s.reg_no} for s in queryset]

        return stores 

    def get_group_list(self):
        groups = UserGroup.objects.filter(
            master_user__email=self.request.user,
            is_owner_group=False
        ).order_by('-id').values('ident_name', 'reg_no')

        groups = list(groups)

        obj_role_reg_no = self.object.role_reg_no

        for group in groups:
            if group['reg_no'] == obj_role_reg_no:
                group['assigned'] = True
            else:
                group['assigned'] = False

        return list(groups)
        

    def get_serializer_context(self):
        context = super(TpEmployeeProfileEditView, self).get_serializer_context()

        context['roles'] = self.get_group_list() 

        context['available_stores'] = self.get_store_list(
            Store.objects.filter(profile__user=self.request.user)
        )
        context['registered_stores'] = self.get_store_list(
            self.object.stores.all()
        )
          
        return context
    
    def put(self, request, *args, **kwargs):
        
        if not self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)
    
        
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():

            self.top_profile = Profile.objects.get(user__email=self.request.user)
            
            # We call get_object here so that 404 would be raised if wrong user
            # tried editing another user's employee profile
            self.employee_profile = self.get_object()

            """ Confirm if store belongs to the top user"""
            stores_info = serializer.validated_data['stores_info']

            self.collected_stores = ApiStoreFormestHelpers.validate_store_reg_nos_for_top_user(
                stores_info, self.top_profile
            )

            if not type(self.collected_stores) == list:
                error_data = {'stores_info': "You provided wrong stores."}
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST)


            # To avoid atomic block error, we verify user group here instead of
            # doint it in the serializer
            group_exists = UserGroup.objects.filter(
                master_user=self.request.user,
                reg_no=serializer.validated_data['role_reg_no'],
                is_owner_group=False
            ).exists()

            if not group_exists:
                error_data = {'role_reg_no': ["Wrong role was selected"]}
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST)

        return self.update(request, *args, **kwargs)
    
    def perform_update(self, serializer):

        serializer.save()

        """
        Adds or removes stores from the passed model
        """
        ApiStoreFormestHelpers.add_or_remove_stores(
            self.employee_profile, 
            self.collected_stores
        )

class TpEmployeeProfileClusterIndexView(generics.ListAPIView):
    queryset = EmployeeProfile.objects.all().select_related('profile', 'user')
    serializer_class = TpEmployeeProfileClusterListSerializer
    permission_classes = (
        permissions.IsAuthenticated, 
        IsTopUserPermission,
        CanViewEmployeesPermission
    )
    pagination_class = StandardResultsSetPagination_10
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ['stores__reg_no']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']

    def get_serializer_class(self):
        return TpEmployeeProfileClusterListSerializer
    
    def get_queryset(self):

        queryset = super(TpEmployeeProfileClusterIndexView, self).get_queryset()

        queryset = queryset.filter(
            profile__user__email=self.request.user
        )

        queryset = queryset.order_by('-id')

        return queryset


class TpEmployeeProfileClusterView(generics.RetrieveUpdateDestroyAPIView):
    queryset = EmployeeProfile.objects.all()
    serializer_class = TpEmployeeClusterViewSerializer
    permission_classes = (
        permissions.IsAuthenticated, 
        IsTopUserPermission,
        CanViewEmployeesPermission
    )
    lookup_field = 'reg_no'

    def get_object(self):

        reg_no = self.kwargs['reg_no']

        """ Check if reg_no is too big"""
        if reg_no > 6000000000000:
            raise Http404
        
        queryset = self.filter_queryset(self.get_queryset())
            
        # Get the single item from the filtered queryset
        self.object = get_object_or_404(queryset)
                   
        # May raise a permission denied
        self.check_object_permissions(self.request, self.object)

        return self.object
    
    def get_queryset(self):
 
        queryset = super(TpEmployeeProfileClusterView, self).get_queryset()
        queryset = queryset.filter(
            profile__user__email=self.request.user, reg_no=self.kwargs['reg_no'])

        return queryset

    """
    Update a model instance.
    """
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid(raise_exception=True):

            # Confirm if clusters belongs to the employee
            self.collected_clusters = ApiWebStoreFormestHelpers.validate_cluster_reg_nos(
                clusters_info=serializer.validated_data['clusters_info'],
            )

            if not type(self.collected_clusters) == dict:
                error_data = {'clusters_info': "You provided wrong clusters."}
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST) 

        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update(self, serializer): 
        
        # Adds or removes clusters from the passed model
        ApiWebStoreFormestHelpers.add_or_remove_clusters(
            model=serializer.instance, 
            collected_clusters=self.collected_clusters['collected_clusters_ids']
        )

        serializer.save() 