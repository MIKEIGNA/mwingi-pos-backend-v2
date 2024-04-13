from rest_framework.permissions import BasePermission

class ManageEmployee(BasePermission):

    message = 'Manageing employees not allowed.'
    def has_permission(self, request, view):
        return request.user.has_perm('profiles.add_employeeprofile')