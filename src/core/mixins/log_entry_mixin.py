from mylogentries.models import UserActivityLog, CREATED, CHANGED, DELETED
from django.utils.encoding import force_str
from django.contrib.contenttypes.models import ContentType
from django.db import router, transaction
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

csrf_protect_m = method_decorator(csrf_protect)

from billing.models import Payment

from core.logging_utils import clean_logging_fields

class AdminUserActivityLogMixin:
    
    @csrf_protect_m
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """
        Everytime an object is added, changed or deleted, this function is called
        """
        
        self.adux_collect_old_values( object_id)
    
        with transaction.atomic(using=router.db_for_write(self.model)):
            return self._changeform_view(request, object_id, form_url, extra_context)

    def adux_collect_old_values(self, object_id):
        """
        Before an object is changed or deleted, this this function gets it's 
        field values and then stores them in a dict called "self.my_old_model_field_dict"
        so that they can be used later to create the log change message 
        """

        self.is_obj_valid = False

        # Collect fields in fieldset
        form_fields_to_track = []
        for fieldset in self.fieldsets:
            form_fields_to_track += list(fieldset[1]['fields'])

        # Remove readonly fields since they can't be tracked
        for readonly_field in self.readonly_fields:
            if readonly_field in form_fields_to_track:
                form_fields_to_track.remove(readonly_field)

        # Check if we have a valid object
        try:
            obj = self.model.objects.get(pk=object_id)
        except:
            obj = None
            
        # Store the object field values and notify the entire class that the 
        # object is valid using the "self.is_obj_valid" variable
        if obj: 
            self.my_model_field_values =form_fields_to_track
            self.is_obj_valid = True
            
            self.my_old_model_field_dict = self.dictify_old_obj(obj)
        
    def make_user_activity_log(self, request, obj, action_type, change_message=''):

        
        try:
            if hasattr(obj, 'get_profile'):
                owner_email = str(obj.get_profile())
            else:
                owner_email = ''
                
            UserActivityLog.objects.create(
                    change_message=change_message,
                    object_id=obj.pk,
                    object_repr=force_str(obj),
                    ip=request.META.get('REMOTE_ADDR', None),
                    content_type=ContentType.objects.get_for_model(obj, for_concrete_model=False),
                    user=request.user,
                    action_type=action_type,
                    owner_email=owner_email,
                    panel='Admin'
                    )
        except Exception as e:            
            request.invalid_msg = '"{}:{}"'.format('UserActivity Failed',e.args)
            

    def log_entry(self, request, obj, new_dict):

        change_message = ''
        for key in self.my_model_field_values:
            old_value = self.my_old_model_field_dict['old_'+key]

            
            new_value = new_dict['new_'+key]
            
            if old_value != new_value:
                if isinstance(obj, Payment):
                    payment_reg_no = obj.subscription.device.reg_no
                    msg = '"{}" for "{}" changed from "{}" to "{}".\n'.format(key.title(), payment_reg_no, old_value, new_value)
                else:
                    msg = '"{}" changed from "{}" to "{}".\n'.format(key.title(), old_value, new_value)
            
                change_message+=msg

        if change_message:
            self.make_user_activity_log(request, obj, CHANGED, change_message)

    def dictify_new_obj(self, obj):
        return self.dictify_obj(obj, 'new')

    def dictify_old_obj(self, obj):
        return self.dictify_obj(obj, 'old')
        
    def dictify_obj(self, obj, slug):
        field_dict = {}
        
        for field in self.my_model_field_values:
            field_name = '{}_{}'.format(slug, field)

            field_dict[field_name] = obj.serializable_value(field)

        return field_dict
        
    def log_addition(self, request, obj, message):
    
        try:
            
            if isinstance(obj, Payment): 
                payment_reg_no = obj.subscription.device.reg_no
                change_message = 'New "{}" "{}" for "{}" has been created by "{}"'.format(obj.__class__.__name__, 
                                                                                        str(obj), 
                                                                                        payment_reg_no ,
                                                                                        request.user
                                                                                        )
            else:
                change_message = 'New "{}" "{}" has been created by "{}"'.format(obj.__class__.__name__, 
                                                                               str(obj), 
                                                                               request.user
                                                                               )
            
            self.make_user_activity_log(request, obj, CREATED, change_message)
        except:
            pass
        
        return super(AdminUserActivityLogMixin, self).log_addition(request, obj, message)
        
        

    def log_change(self, request, obj, message):

        try:
            if self.is_obj_valid:
                my_new_model_field_dict = self.dictify_new_obj(obj)
                self.log_entry(request, obj, my_new_model_field_dict)
        except:
            pass

        return super(AdminUserActivityLogMixin, self).log_change(request, obj, message)
    
    def log_deletion(self, request, obj, object_repr):
        
        if isinstance(obj, Payment): 
            payment_reg_no = obj.account_reg_no
            change_message = '"{}" for "{}" has been deleted by "{}"'.format(str(obj), payment_reg_no ,request.user)
        else:
            change_message = '"{}" has been deleted by "{}"'.format(str(obj), request.user)
        
        self.make_user_activity_log(request, obj, DELETED, change_message)
        
        return super(AdminUserActivityLogMixin, self).log_deletion(request, obj, object_repr)
        
        
        
class UserActivityLogMixin:
    new_api_user = False
    api_panel_name = 'Api'
    web_panel_name = 'Web'
    
    def make_user_activity_log(self, obj, action_type, change_message=''):
   
        try:
            # Chekc if the current user is logged in on behalf of another user
            login_as_user_email = self.request.session.get('request_logged_in_as_user', None)

            hijacked = False

            if login_as_user_email:
                hijacked = True
                active_user = get_user_model().objects.get(email=login_as_user_email)
  
            else:
                active_user = self.request.user

            # Check if the object being logged has a get profile method
            if hasattr(obj, 'get_profile'):
                owner_email = str(obj.get_profile())
            else:
                owner_email = ''
            
            UserActivityLog.objects.create(
                    change_message = change_message,
                    object_id = obj.pk,
                    object_repr = force_str(obj),
                    ip = self.request.META.get('REMOTE_ADDR', None),
                    content_type = ContentType.objects.get_for_model(obj, for_concrete_model=False),
                    user = obj if self.new_api_user else active_user,
                    action_type = action_type,
                    owner_email = owner_email,
                    panel = self.used_panel,
                    is_hijacked=hijacked
                    )
        except Exception as e: 
            
            invalid_message =  '"{}:{}"'.format('UserActivity Failed',e.args)
            
            self.request.invalid_msg = invalid_message
                
    """ These are called by the API Views"""
    def ux_log_new_user_api(self, obj, include_value):
        self.used_panel = self.api_panel_name
        self.new_api_user = True
        self.log_new_object(obj, include_value)
    
    def ux_log_new_object_api(self, obj, include_value):
        self.used_panel = self.api_panel_name
        self.log_new_object(obj, include_value)
        
    def ux_log_changed_fields_api(self):
        self.used_panel = self.api_panel_name
        self.log_changed_fields()
       
    def create(self, request, *args, **kwargs):
        """
        This is used by Api Views that implement the CreateModelMixin
        
        When a serializer is not valid and has errors during a new model 
        creation process, this overriden method is used for creating 
        invalid_msg to be logged.
        """
    
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():  
            data = dict(serializer.data)
            
            """ This will remove sensitive info like passwords """
            data = clean_logging_fields(data)
                        
            message = '"{}<=>{}{}<=>{}"'.format('form_invalid', dict(serializer.errors), dict(serializer.errors), data)
            
        
            self.request._request.invalid_msg = message

        
        return super(UserActivityLogMixin, self).create(request, *args, **kwargs)
        
    
    def update(self, request, *args, **kwargs):
        """
        This is used by Api Views that implement the UpdateModelMixin
        
        When a serializer is not valid and has errors during a model update 
        process, this overriden method is used for creating invalid_msg to be 
        logged.
        """

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if not serializer.is_valid():
            
            data = dict(serializer.data)
            
            """ This will remove sensitive info like passwords """
            data = clean_logging_fields(data)
            
            
            message = '"{}<=>{}{}<=>{}"'.format('form_invalid', dict(serializer.errors), dict(serializer.errors), data)
            
            self.request._request.invalid_msg = message
        
        return super(UserActivityLogMixin, self).update(request, *args, **kwargs)
        
        
        
    """ These are called by the Web Views """
    def ux_log_new_object(self, obj, include_value):
        self.used_panel = self.web_panel_name
        self.log_new_object(obj, include_value)
        
        
    def ux_fields_to_log(self, field_list):
        self.my_model_field_values = field_list
        self.my_old_model_field_dict = self.dictify_obj(self.obj, 'old')
            
        
    def ux_log_changed_fields(self):
        self.used_panel = self.web_panel_name
        self.log_changed_fields()
        
        
    def form_invalid(self, form):
        """
        This is used by Web Views
        
        When a form is not valid and has errors, this overriden method is 
        used for creating invalid_msg to be logged.
        """
        
        
        """
        Get the error as a text and then assign to self.request.invalid_msg so
        that it can be logged by the AuditLoggingMiddleware 
        """
        error_text = form.errors.as_text().replace('\n', '')
        
    
        fields = form.data.dict()
        
        """ If fields has 'csrfmiddlewaretoken', remove it """
        fields.pop('csrfmiddlewaretoken') if fields.get('csrfmiddlewaretoken', None) else ''
    
                
        """
        If passwords are in the fields, replace them with *************
        to avoid real passwords being logged
        """
        if fields.get('password', None):
            fields['password'] = '*********'
            
        if fields.get('password1', None):
            fields['password1'] = '*********'

        if fields.get('password2', None):
            fields['password2'] = '*********'

        message = '"{}:{}{}"'.format('form_invalid', error_text, fields)
        
        self.request.invalid_msg = message
        

        return super(UserActivityLogMixin, self).form_invalid(form)
        
     
        
    """ These methods are called by the above Web and Api views which are 
        View abstraction layers
    """
    def log_new_object(self, obj, include_value):

        request_user = obj if self.new_api_user else self.request.user
        
        change_message = 'New {} "{}" has been created by "{}"'.format(obj.__class__.__name__, 
                                                                       include_value, 
                                                                       request_user
                                                                       )
        self.make_user_activity_log(obj, CREATED, change_message)
            
    def log_changed_fields(self):
        my_new_model_field_dict = self.dictify_new_obj(self.obj)
        self.log_entry(self.obj, my_new_model_field_dict)

    def dictify_new_obj(self, obj):
        return self.dictify_obj(obj, 'new')
           
    def dictify_obj(self, obj, slug):
        field_dict = {}
        
        for field in self.my_model_field_values:
            field_name = '{}_{}'.format(slug, field)
            field_dict[field_name] = obj.serializable_value(field)
            
        return field_dict
    
    def log_entry(self, obj, new_dict):
        change_message = ''
        for key in self.my_model_field_values:
            old_value = self.my_old_model_field_dict['old_'+key]
            new_value = new_dict['new_'+key]
            
            if old_value != new_value:
                msg = '{} changed from "{}" to "{}".\n'.format(key.title(), old_value, new_value)
                change_message+=msg
                
        if change_message:
            self.make_user_activity_log(obj, CHANGED, change_message)
            
        return True
            
            