from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status

from api.utils.permission_helpers.api_view_permissions import CanViewEmployeesPermission, IsTopUserPermission
from api.utils.api_pagination import LeanResultsSetPagination
from api.serializers.profiles.role_serializers import (
    LeanRoleListCreateSerializer,
    RoleEditViewSerializer, 
    RoleListCreateSerializer
)

from accounts.create_permissions import PermissionHelpers
from accounts.models import UserGroup


class LeanRoleIndexView(generics.ListCreateAPIView):
    queryset = UserGroup.objects.all()
    serializer_class = LeanRoleListCreateSerializer
    permission_classes = (
        permissions.IsAuthenticated, 
        IsTopUserPermission,
        CanViewEmployeesPermission
    )
    pagination_class = LeanResultsSetPagination
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(LeanRoleIndexView, self).get_queryset()
        
        queryset = queryset.filter(
            master_user__email=self.request.user,
            is_owner_group=False
        )
        queryset = queryset.order_by('-id')

        return queryset

class RoleIndexView(generics.ListCreateAPIView):
    queryset = UserGroup.objects.all()
    serializer_class = RoleListCreateSerializer
    permission_classes = (
        permissions.IsAuthenticated, 
        IsTopUserPermission,
        CanViewEmployeesPermission
    )
    pagination_class = LeanResultsSetPagination
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(RoleIndexView, self).get_queryset()
        
        queryset = queryset.filter(
            master_user__email=self.request.user,
            is_owner_group=False)
        queryset = queryset.order_by('-id')

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
            current_user=self.request.user)

    def perform_create(self, serializer):
        
        try:
            self.create_user_group(serializer)
        except: # pylint: disable=bare-except
            " log this "
        
    def create_user_group(self, serializer):

        user = self.request.user
        group_name = serializer.validated_data['ident_name']

        group = UserGroup.objects.create(
                master_user=user, 
                name=f'{group_name} {user.reg_no}',
                ident_name=group_name,
            )
        perms = {
            'can_view_shift_reports': serializer.validated_data['can_view_shift_reports'],
            'can_manage_open_tickets': serializer.validated_data['can_manage_open_tickets'],
            'can_void_open_ticket_items': serializer.validated_data['can_void_open_ticket_items'],
            'can_manage_items': serializer.validated_data['can_manage_items'],
            'can_refund_sale': serializer.validated_data['can_refund_sale'],
            'can_open_drawer': serializer.validated_data['can_open_drawer'],
            'can_reprint_receipt': serializer.validated_data['can_reprint_receipt'],
            'can_change_settings': serializer.validated_data['can_change_settings'],
            'can_apply_discount': serializer.validated_data['can_apply_discount'],
            'can_change_taxes': serializer.validated_data['can_change_taxes'],
            'can_accept_debt': serializer.validated_data['can_accept_debt'],
            'can_manage_customers': serializer.validated_data['can_manage_customers'],
            'can_manage_employees': serializer.validated_data['can_manage_employees'],
            'can_change_general_settings': serializer.validated_data['can_change_general_settings'],
        } 

        # Assign the selected permissions
        PermissionHelpers.assign_group_permissions(group, perms)

class RoleEditView(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserGroup.objects.all()
    serializer_class = RoleEditViewSerializer
    permission_classes = (
        permissions.IsAuthenticated, 
        IsTopUserPermission,
        CanViewEmployeesPermission
    )
    lookup_field = 'reg_no'
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her object
        """
        queryset = super(RoleEditView, self).get_queryset()
        queryset = queryset.filter(
            master_user__email=self.request.user,
            reg_no=self.kwargs['reg_no']
        )

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
            current_user=self.request.user,
            group_reg_no=self.kwargs['reg_no'])

    def put(self, request, *args, **kwargs):
        
        if self.get_object().is_owner_group:
            return Response(status=status.HTTP_403_FORBIDDEN)

        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):

        if self.get_object().is_owner_group:
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        return super(RoleEditView, self).delete(request, *args, **kwargs)

    def perform_update(self, serializer):

        user = self.request.user
        group_name = serializer.validated_data['ident_name']

        serializer.save(name=f'{group_name} {user.reg_no}')

        perms = {
            'can_view_shift_reports': serializer.validated_data['can_view_shift_reports'],
            'can_manage_open_tickets': serializer.validated_data['can_manage_open_tickets'],
            'can_void_open_ticket_items': serializer.validated_data['can_void_open_ticket_items'],
            'can_manage_items': serializer.validated_data['can_manage_items'],
            'can_refund_sale': serializer.validated_data['can_refund_sale'],
            'can_open_drawer': serializer.validated_data['can_open_drawer'],
            'can_reprint_receipt': serializer.validated_data['can_reprint_receipt'],
            'can_change_settings': serializer.validated_data['can_change_settings'],
            'can_apply_discount': serializer.validated_data['can_apply_discount'],
            'can_change_taxes': serializer.validated_data['can_change_taxes'],
            'can_accept_debt': serializer.validated_data['can_accept_debt'],
            'can_manage_customers': serializer.validated_data['can_manage_customers'],
            'can_manage_employees': serializer.validated_data['can_manage_employees'],
            'can_change_general_settings': serializer.validated_data['can_change_general_settings'],
        }

        # Assign the selected permissions
        PermissionHelpers.assign_group_permissions(serializer.instance, perms)
