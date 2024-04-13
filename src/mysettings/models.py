from django.db import models
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from rest_framework.authtoken.models import Token

User = get_user_model()

class MySetting(models.Model):
    name = models.CharField(
        verbose_name='name',
        max_length=300,
        editable=False,
        unique=True,)
    reset_tokens = models.BooleanField(
            verbose_name='reset tokens',
            default=False)
    signups = models.BooleanField(
            verbose_name='signups',
            default=True)
    maintenance = models.BooleanField(
            verbose_name='maintenance',
            default=True)
    allow_contact = models.BooleanField(
            verbose_name='allow contact',
            default=True)
    delete_sessions = models.BooleanField(
            verbose_name='delete sessions',
            default=False)
    accept_payments = models.BooleanField(
            verbose_name='accept payments',
            default=True)
    accept_mpesa = models.BooleanField(
            verbose_name='accept mpesa',
            default=True)
    new_employee = models.BooleanField(
            verbose_name='new employee',
            default=True)
    new_product = models.BooleanField(
            verbose_name='new product',
            default=True)
    new_customer = models.BooleanField(
            verbose_name='new customer',
            default=True)
    new_sale = models.BooleanField(
            verbose_name='new sale',
            default=True)
    new_sale = models.BooleanField(
            verbose_name='new sale',
            default=True)
    receipt_change_stock_task_running = models.BooleanField(
            verbose_name='stock task running',
            default=False)
    stock_task_update_date = models.DateTimeField(
        verbose_name="stock task update date",
        default=timezone.now,
    )
    
    def __str__(self):
        return str(self.name)
    
    def logout_users(self):
        """ 
           If maintenance is turned to true and the previous one was false, 
           logout every user
        """
        try:
            my_setting = MySetting.objects.get(name='main')
            
            old_maint = my_setting.maintenance

        # pylint: disable=bare-except
        except:
            old_maint = False
            
        new_maint = self.maintenance
        
        if new_maint and not old_maint:
            self.delete_sessions = True
            return True
            
        return False
    
    def regenerate_tokens(self):
        """ Deletes all tokens and then generate new ones of each user """
        Token.objects.all().delete() # delete tokens
        users = User.objects.all()
        for user in users:            
            Token.objects.get_or_create(user=user)
            
        """ Set my MySetting's regenerate_tokens back to false """
        self.reset_tokens = False
        
        return True
            
    def save(self, *args, **kwargs):
        if self.maintenance:
            self.logout_users()
        
        if self.reset_tokens:
            self.regenerate_tokens()
            
        super(MySetting, self).save(*args, **kwargs) # Call the "real" save() method.
        
    def delete(self, *args, **kwargs):
        pass
        
@receiver(post_save, sender=MySetting)
def delete_sessions_and_tokens(sender, instance, created, **kwargs):
    """ Delete all sessions and tokens """
    if instance.delete_sessions:
        Session.objects.all().delete() # delete sessions
    
        """ Create new tokens for each user """
        instance.regenerate_tokens()
            
        """ Turn the delete_sessions to false """
        instance.delete_sessions = False
        instance.save()
