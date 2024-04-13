from django import forms
from django.contrib.auth import get_user_model

from core.core_forms import MyTextInput

User = get_user_model()


class UserCreationAdminForm(forms.ModelForm):
    """A form for creating new users in the admin area. Includes all the required
    password fields, plus a repeated password.
    """
    
    def __init__(self, *args, **kwargs):
        super(UserCreationAdminForm, self).__init__(*args, **kwargs)
        self.fields['phone'].widget=MyTextInput()
    
    password1 = forms.CharField(
            label='Password', 
            widget=forms.PasswordInput)
    password2 = forms.CharField(
            label='Password confirmation', widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone')
        
    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationAdminForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user