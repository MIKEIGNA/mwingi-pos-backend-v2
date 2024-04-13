from django.conf import settings
from django.http.response import Http404
import django_filters

from rest_framework import generics
from rest_framework import permissions
from rest_framework.exceptions import Throttled
from rest_framework.response import Response
from rest_framework import status
from rest_framework import filters

from api.serializers.products.modifier_serializers import (
    LeanModifierListSerializer, 
    ModifierViewSerializer
)

from api.utils.api_pagination import LeanResultsSetPagination
from api.utils.api_view_formset_utils import ApiEmployeeStoreFormestHelpers, ApiStoreFormestHelpers
from api.utils.api_view_modifier_formset_utils import ApiModifierOptionsFormestHelpers
from api.utils.api_web_pagination import StandardWebResultsAndStoresSetPagination
from api.utils.permission_helpers.api_view_permissions import IsEmployeeUserPermission, ItemPermission

from core.mixins.log_entry_mixin import UserActivityLogMixin
from api.serializers import ModifierListSerializer
from core.my_throttle import ratelimit

from products.models import Modifier, ModifierOption
from profiles.models import EmployeeProfile
from stores.models import Store

class EpLeanModifierIndexView(UserActivityLogMixin, generics.ListCreateAPIView):
    queryset = Modifier.objects.all()
    serializer_class = LeanModifierListSerializer
    permission_classes = (permissions.IsAuthenticated, IsEmployeeUserPermission)
    pagination_class = LeanResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name',]

    def get_queryset(self):
       
        queryset = super(EpLeanModifierIndexView, self).get_queryset()
        queryset = queryset.filter(
            stores__employeeprofile__user=self.request.user,
        ).distinct().order_by('-id')

        return queryset


class EpModifierIndexView(UserActivityLogMixin, generics.ListCreateAPIView):
    queryset = Modifier.objects.all()
    serializer_class = ModifierListSerializer
    permission_classes = (
        permissions.IsAuthenticated, 
        ItemPermission, 
        IsEmployeeUserPermission
    )
    pagination_class = StandardWebResultsAndStoresSetPagination
    filter_backends = [
        filters.SearchFilter, 
        django_filters.rest_framework.DjangoFilterBackend
    ]
    filterset_fields = ['stores__reg_no', ]
    search_fields = ['name',]

    def get_queryset(self):
       
        queryset = super(EpModifierIndexView, self).get_queryset()
        queryset = queryset.filter(
            stores__employeeprofile__user=self.request.user,
        ).distinct().order_by('-id')

        return queryset

    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(
            *args, 
            **kwargs, 
            current_user_profile=self.request.user.employeeprofile.profile)

    @ratelimit(
        scope='api_ip', 
        rate=settings.THROTTLE_RATES['api_modifier_rate'], 
        alt_name='api_modifier_create'
    )
    def post(self, request, *args, **kwargs):

        # if api_throttled is in kwargs, throttle the view 
        if kwargs.get('request_throttled', None):
            response = self.handle_exception(Throttled(1))
            self.response = self.finalize_response(request, response, *args, **kwargs)
            
            return self.response
        
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():

            """ Confirm if stores belongs to the store"""
            stores_info = serializer.validated_data['stores_info']

            # Confirm if store belongs to the employee user
            self.manager_employee_profile = EmployeeProfile.objects.get(user=self.request.user)

            self.collected_stores = ApiEmployeeStoreFormestHelpers.validate_store_reg_nos_for_manager_user(
                stores_info, self.manager_employee_profile,
            )

            if not type(self.collected_stores) == list:
                error_data = {'stores_info': "You provided wrong stores."}
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST) 

            # Check if options have unique names
            option_names = []
            for opt in serializer.validated_data['modifier_options']:

                if opt['name'] in option_names:
                    return Response(
                        {'non_field_errors': 'Options must have unique names.'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    ) 

                option_names.append(opt['name'])

        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        
        try:
            return self.create_modifier(serializer)
        except: # pylint: disable=bare-except
            """ log here """

        return True

    def create_modifier(self, serializer):

        modifier = Modifier.objects.create(
            profile=self.manager_employee_profile.profile,
            name=serializer.validated_data['name'],
        )

        options = serializer.validated_data['modifier_options']

        for opt in options:

            ModifierOption.objects.create(
                modifier=modifier,
                name=opt['name'],
                price=opt['price'],
        )

        modifier.stores.add(*self.collected_stores)


class EpModifierView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Modifier.objects.all()
    serializer_class = ModifierViewSerializer
    permission_classes = (
        permissions.IsAuthenticated, 
        ItemPermission,
        IsEmployeeUserPermission
    )
    lookup_field = 'reg_no'
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her object
        """
        self.employee_profile = EmployeeProfile.objects.get(user=self.request.user)
        self.profile = self.employee_profile.profile

        queryset = super(EpModifierView, self).get_queryset()
        queryset = queryset.filter(
            stores__employeeprofile=self.employee_profile, 
            reg_no=self.kwargs['reg_no'],
        ).distinct()

        return queryset

    def get_object(self):

        """ Check if reg_no is too big"""
        if self.kwargs['reg_no'] > 6000000000000:
            raise Http404
     
        self.obj = super(EpModifierView, self).get_object()
        return self.obj

    def get_store_list(self, queryset):
        """
        Returns a list with dicts that have store names and reg_nos
        """
        queryset = queryset.order_by('id')
        stores = [{'name': s.name, 'reg_no': s.reg_no} for s in queryset]

        return stores

    def get_serializer_context(self):
        context = super(EpModifierView, self).get_serializer_context()

        context['available_stores'] = self.get_store_list(
            Store.objects.filter(employeeprofile=self.employee_profile)
        )
        context['registered_stores'] = self.get_store_list(
            self.obj.stores.all()
        )
          
        return context

    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(
            *args, 
            **kwargs, 
            current_user_profile=self.profile,
            modifier_reg_no=self.kwargs['reg_no']
        )

    """
    Update a model instance.
    """
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid(raise_exception=True):

            """ Confirm if store belongs to the top user"""
            stores_info = serializer.validated_data['stores_info']
            
            # Confirm if store belongs to the employee user
            self.manager_employee_profile = EmployeeProfile.objects.get(user=self.request.user)

            self.collected_stores = ApiEmployeeStoreFormestHelpers.validate_store_reg_nos_for_manager_user(
                stores_info, self.manager_employee_profile
            )

            if not type(self.collected_stores) == list:
                error_data = {'stores_info': "You provided wrong stores."}
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST)

            try:
            
                """ Update options"""
                options_info = serializer.validated_data['options_info']

                ApiModifierOptionsFormestHelpers.update_modifier_options(
                    options_info=options_info,
                    modifier=self.obj
                )         

            except: # pylint: disable=bare-except
                return Response(status=status.HTTP_404_NOT_FOUND)

        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update(self, serializer):

        serializer.save()

        """
        Adds or removes stores from the passed model
        """
        ApiStoreFormestHelpers.add_or_remove_stores(
            serializer.instance, 
            self.collected_stores
        )

