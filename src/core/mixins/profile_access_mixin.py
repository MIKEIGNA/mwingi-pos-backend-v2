from django.http import Http404

from accounts.utils.user_type import EMPLOYEE_USER, TOP_USER


"""
For this mixin to block non superusers, it should be placed before 
LoginRequiredMixin
"""


class SuperUserAccessMixin:

    def dispatch(self, request, *args, **kwargs):

        # Raise 404 if user is not superuser
        if self.request.user.is_superuser:
            return super(SuperUserAccessMixin, self).dispatch(request, *args, **kwargs)

        raise Http404


class TopProfileAccessMixin:
    def dispatch(self, request, *args, **kwargs):

        # Raise 404 if user is not top user
        if getattr(self.request.user, 'user_type', None) == TOP_USER:
            return super(TopProfileAccessMixin, self).dispatch(request, *args, **kwargs)

        raise Http404


class ManagerEmployeeProfileAccessMixin:

    def dispatch(self, request, *args, **kwargs):

        # Raise 404 if user is not supervisor user
        if getattr(self.request.user, 'user_type', None) == EMPLOYEE_USER:
            return super(ManagerEmployeeProfileAccessMixin, self).dispatch(request, *args, **kwargs)

        raise Http404


class EmployeeProfileAccessMixin:

    def dispatch(self, request, *args, **kwargs):

        # Raise 404 if user is not team user
        if getattr(self.request.user, 'user_type', None) == EMPLOYEE_USER:
            return super(EmployeeProfileAccessMixin, self).dispatch(request, *args, **kwargs)

        raise Http404
