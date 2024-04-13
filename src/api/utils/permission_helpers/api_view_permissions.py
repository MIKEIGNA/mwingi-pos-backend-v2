
from rest_framework import permissions

from accounts.utils.user_type import TOP_USER

class IsSuperUserPermission(permissions.BasePermission):
    """
    Global permission for superuser.
    """

    edit_methods = ("PUT", "PATCH", "POST", "DELETE")

    def has_permission(self, request, view):
        return request.user.is_superuser

class IsTopUserPermission(permissions.BasePermission):
    """
    Global permission for top user.
    """

    edit_methods = ("PUT", "PATCH", "POST", "DELETE")

    def has_permission(self, request, view):
        return request.user.user_type == TOP_USER

class IsEmployeeUserPermission(permissions.BasePermission):
    """
    Global permission for employee user.
    """

    edit_methods = ("PUT", "PATCH", "POST", "DELETE")

    def has_permission(self, request, view):
        return not request.user.user_type == TOP_USER
    
class ViewCustomersPermission(permissions.BasePermission):
    """
    Global permission check for blocked IPs.
    """

    edit_methods = ("PUT", "PATCH", "POST", "DELETE")

    def has_permission(self, request, view):

        if request.method in self.edit_methods:
            return request.user.has_perm('accounts.can_manage_items')

        return True

class ItemPermission(permissions.BasePermission):
    """
    Global permission check for blocked IPs.
    """

    edit_methods = ("PUT", "PATCH", "POST", "DELETE")

    def has_permission(self, request, view):

        if request.method in self.edit_methods:
            return request.user.has_perm('accounts.can_manage_items')

        return True


class RefundPermission(permissions.BasePermission):
    """
    Global permission check for blocked IPs.
    """

    edit_methods = ("PUT", "PATCH", "POST", "DELETE")

    def has_permission(self, request, view):

        if request.method in self.edit_methods:
            return request.user.has_perm('accounts.can_refund_sale')

        return True


class OpenTicketManagePermission(permissions.BasePermission):
    """
    Global permission check for blocked IPs.
    """

    edit_methods = ("GET", "PUT", "PATCH", "POST", "DELETE")

    def has_permission(self, request, view):

        if request.method in self.edit_methods:
            return request.user.has_perm('accounts.can_manage_open_tickets')

        return True

class OpenTicketVoidPermission(permissions.BasePermission):
    """
    Global permission check for blocked IPs.
    """

    edit_methods = ("PUT", "PATCH", "POST", "DELETE")

    def has_permission(self, request, view):

        if request.method in self.edit_methods:
            return request.user.has_perm('accounts.can_void_open_ticket_items')

        return True


class CanViewUserSettingsPermission(permissions.BasePermission):
    """
    Global permission check for blocked IPs.
    """

    edit_methods = ("PUT", "PATCH", "POST", "DELETE")

    def has_permission(self, request, view):
        return request.user.has_perm('accounts.can_view_settings')
    
class CanViewStoresPermission(permissions.BasePermission):
    """
    Global permission check for blocked IPs.
    """

    edit_methods = ("PUT", "PATCH", "POST", "DELETE")

    def has_permission(self, request, view):
        return request.user.has_perm('accounts.can_view_stores')
    
class CanViewClustersPermission(permissions.BasePermission):
    """
    Global permission check for blocked IPs.
    """

    edit_methods = ("PUT", "PATCH", "POST", "DELETE")

    def has_permission(self, request, view):
        return request.user.has_perm('accounts.can_view_clusters')
    
class CanViewCustomersPermission(permissions.BasePermission):
    """
    Global permission check for blocked IPs.
    """

    edit_methods = ("PUT", "PATCH", "POST", "DELETE")

    def has_permission(self, request, view):
        return request.user.has_perm('accounts.can_view_customers')
        
class CanViewItemsPermission(permissions.BasePermission):
    """
    Global permission check for blocked IPs.
    """

    edit_methods = ("GET", "PUT", "PATCH", "POST", "DELETE")

    def has_permission(self, request, view):
        return request.user.has_perm('accounts.can_view_items')
    
class CanViewEmployeesPermission(permissions.BasePermission):
    """
    Global permission check for blocked IPs.
    """

    edit_methods = ("GET", "PUT", "PATCH", "POST", "DELETE")

    def has_permission(self, request, view):
        return request.user.has_perm('accounts.can_view_employees')
    
class CanViewInventoryPermission(permissions.BasePermission):
    """
    Global permission check for blocked IPs.
    """

    edit_methods = ("GET", "PUT", "PATCH", "POST", "DELETE")

    def has_permission(self, request, view):
        return request.user.has_perm('accounts.can_view_inventory')