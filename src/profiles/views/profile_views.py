from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.views.generic import UpdateView, DetailView

from core.mixins.log_entry_mixin import UserActivityLogMixin
from core.mixins.profile_access_mixin import TopProfileAccessMixin

from core.my_throttle import ratelimit 

from profiles.models import Profile
from profiles.forms import ProfileEditForm, ProfilePictureForm


class ProfileView(LoginRequiredMixin, TopProfileAccessMixin, DetailView):
    model = Profile
    template_name = 'profiles/tp_profile.html'

    def get_object(self):

        queryset = self.get_queryset().select_related('user')

        self.obj = get_object_or_404(queryset, user__email=self.request.user)

        return self.obj

    def get_context_data(self, ** kwargs):
        context = super(ProfileView, self).get_context_data(** kwargs)

        user_details = {
            'full_name': self.obj.get_full_name(),
            'profile_image_url': self.obj.get_profile_image_url(),
            'email': self.obj.user.email,
            'phone': self.obj.user.phone,
            'location': self.obj.get_location(),
            'currency': self.obj.get_currency_initials(),
            'join_date': self.obj.get_join_date(self.request.user.get_user_timezone()),
            'last_login': self.obj.get_last_login_date(self.request.user.get_user_timezone()),
            'edit_profile_image_url': 'profiles:edit_profile_image',
            'edit_profile_url': 'profiles:edit_profile'
        }

        context['user_details'] = user_details

        return context


class EditProfileView(LoginRequiredMixin, TopProfileAccessMixin, UserActivityLogMixin, UpdateView):
    template_name = 'profiles/tp_edit_profile_form.html'
    form_class = ProfileEditForm
    success_url = ''  # This has been overriden below
    model = Profile

    def get_object(self):
        """ 
        For UX logger to work, the model should be stored in a variable
        named "self.obj" in the view instance
        """
        self.obj = get_object_or_404(
            self.get_queryset(), user__email=self.request.user)

        """ Get form fields to log """
        self.ux_fields_to_log(self.get_form_class().base_fields)

        return self.obj

    def form_valid(self, form):
        """ Log changed fields """
        self.ux_log_changed_fields()

        return super(EditProfileView, self).form_valid(form)

    def get_form_kwargs(self):
        # Sending user object to the form

        kwargs = super(EditProfileView, self).get_form_kwargs()

        kwargs.update({'user': self.request.user})

        return kwargs

    def get_success_url(self):
        """
        Upon a successful profile edit, redirects to profile view
        """
        return reverse_lazy('profiles:profile')


class EditProfilePictureView(LoginRequiredMixin, TopProfileAccessMixin, UpdateView):
    template_name = 'profiles/tp_edit_profile_image_form.html'
    form_class = ProfilePictureForm
    success_url = ''  # This has been overriden below
    model = Profile

    """ For Throttling """
    block_url = 'accounts_too_many_requests'

    """
    The report_create value used in alt_name, is used to make the cache key unique
    so that it can only apply to report create views.
    
    Example --> teams.views_mixin.report_create.dispatch_1_8/60s1557486502
    """

    @ratelimit(
        scope='user', 
        rate=settings.THROTTLE_RATES['profile_image_rate'], 
        alt_name='profile_image_rate'
    )
    def post(self, request, *args, **kwargs):
        return super(EditProfilePictureView, self).post(request, *args, **kwargs)

    def get_object(self):
        self.obj = get_object_or_404(
            self.get_queryset(), user__email=self.request.user)
        return self.obj

    def get_success_url(self):
        """
        Upon a successful profile image change, redirects to profile view
        """
        return reverse_lazy('profiles:profile')
