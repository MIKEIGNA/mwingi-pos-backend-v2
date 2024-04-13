from django.contrib.auth import get_user_model

from profiles.models import Profile

User = get_user_model()


class UserFormCleanPhoneNumbersMixin:
    
    def clean_phone(self):
        phone = self.cleaned_data['phone']
        
        if self.user:
            current_user_email = self.user.email
            
            phone_exists = User.objects.filter(phone=phone
                                                  ).exclude(email=current_user_email
                                                  ).exists()
            
            if self.user and phone_exists:
                self.add_error('phone', "User with this phone already exists.")
                
        return phone

    

    