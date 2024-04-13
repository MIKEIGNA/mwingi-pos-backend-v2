from django import forms
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model

from core.core_forms import MyTextInput

User = get_user_model()
    
class MakePaymentForm(forms.Form):
    
    def __init__(self, *args, **kwargs):
        super(MakePaymentForm, self).__init__(*args, **kwargs)
        
        self.fields['account_no'].widget=MyTextInput()
        self.fields['amount'].widget=MyTextInput()
    
    account_no = forms.IntegerField(
        validators=[MinValueValidator(0)]
    )
    amount = forms.IntegerField(
        validators=[MinValueValidator(0)]
    )
    
    def clean_account_no(self):
        reg_no = self.cleaned_data['account_no']
        
        error_msg = 'That registration number is not recognized.'.format(reg_no)
        
        if reg_no > 6000000000000:
            raise forms.ValidationError(error_msg)
            
        

        user_exists = User.objects.filter(reg_no=reg_no).exists()
                    
        if not user_exists:
            raise forms.ValidationError(error_msg)
            
        return reg_no

