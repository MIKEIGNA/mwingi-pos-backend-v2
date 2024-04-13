from django.forms.widgets import TextInput, Textarea, PasswordInput
from django import forms
from django.core.exceptions import ValidationError


class MqModelForm(forms.ModelForm): 
    
    def add_error(self, field, error):
        """
        When using postgresql, when a user enters a very long number on a BigIntegerField
        it raises the following error:
            "Ensure this value is less than or equal to 9223372036854775807."
            
        This error is not so user friendly so we override it so that we just raise
        "This number is too long" error
        """
        
        if "9223372036854775807" in str(error):
            error = ValidationError('This number is too long.')
            
        super(MqModelForm, self).add_error(field, error)


class MyInputMixin:
    def get_context(self, name, value, attrs):
        context = super(MyInputMixin, self).get_context(name, value, attrs)
        context['widget']['attrs'] = {'class': 'form-control',
#                                       'required': '',
#                                       'autofocus': '',
                                       }
                
        return context
         
class MyTextInput(MyInputMixin, TextInput): 
    pass

class MyTextarea(MyInputMixin, Textarea): 
    pass

class MyPasswordInput(MyInputMixin, PasswordInput): 
    pass

class PolyTextareaMixin:
    def get_context(self, name, value, attrs):
        context = super(PolyTextareaMixin, self).get_context(name, value, attrs)
        context['widget']['attrs'] = {'class': 'form-control',
                                      'id':'form-coords',
#                                       'required': '',
                                       'autofocus': ''}
                
        return context
     
class MyPolyInput(PolyTextareaMixin, Textarea): 
    pass


class ReportQuestionTextareaMixin:
    def get_context(self, name, value, attrs):
        context = super(ReportQuestionTextareaMixin, self).get_context(name, value, attrs)
        context['widget']['attrs'] = {'class': 'form-control',
#                                       'required': '',
                                       'autofocus': ''}
                
        return context
     
class ReportQuestionTextarea(ReportQuestionTextareaMixin, Textarea): 
    pass


class InvoiceSaleTextareaMixin:
    def get_context(self, name, value, attrs):
        context = super(InvoiceSaleTextareaMixin, self).get_context(name, value, attrs)
        context['widget']['attrs'] = {'class': 'form-control',
#                                       'required': '',
                                       'autofocus': ''}
                
        return context
class InvoiceSaleTextarea(InvoiceSaleTextareaMixin, Textarea): 
    pass



