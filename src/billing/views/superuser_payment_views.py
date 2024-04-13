
from django.views.generic import FormView
from django.views import View
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.http import Http404

from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from core.my_settings import MySettingClass
from core.mixins.log_entry_mixin import UserActivityLogMixin
from core.mixins.profile_access_mixin import SuperUserAccessMixin

from accounts.utils.validators import validate_safaricom_number

from ..utils.payment_utils.accept_payment import AcceptPayment
from ..mpesa_serializer import MpesaSerializer
from ..forms import MakePaymentForm 

class SuperPaymentCompleteView(SuperUserAccessMixin, View):
    template_name = 'billing/superuser_payment_completed.html'
    
    def get(self, request, * args, ** kwargs):
        return render(request, self.template_name)

class SuperPaymentsNotAllowedView(SuperUserAccessMixin, View):
    template_name = 'billing/superuser_payments_not_allowed.html'
    
    def get(self, request, * args, ** kwargs):
        return render(request, self.template_name) 
    
class SuperUserPaymentDispatchMixin:   
    
    def dispatch(self, request, *args, **kwargs):
        accept_payments = MySettingClass.accept_payments()
        
        """ Verify user is a superuser"""
        if not self.request.user.is_superuser:
            raise Http404
        
        """ Ensure new payments are allowed """
        if not accept_payments:
            return HttpResponseRedirect(reverse_lazy('billing:super_payment_not_allowed'))
    
        return super(SuperUserPaymentDispatchMixin, self).dispatch(request, *args,**kwargs)

class MakePaymentView(SuperUserPaymentDispatchMixin, UserActivityLogMixin, FormView):
    template_name = 'billing/make_payment_form.html'
    form_class = MakePaymentForm
    success_url = reverse_lazy('billing:super_payment_complete')

    
    def form_valid(self, form):
    
        reg_no = form.cleaned_data.get('account_no')
        amount = form.cleaned_data.get('amount')
        
        complete_payment_info = {"payment_method": "manual_payment",
                                 "request_type": "confirmation",
                                 "payment_info": {'reg_no': reg_no,
                                                  'amount': amount
                                                  }
                                 }
    
        payment_accepted, error_result = AcceptPayment(**complete_payment_info).accept_payments()
        
        
        if not payment_accepted:
            
            form.errors['account_no'] = ["An Error Found - {}".format(error_result)]
                    
            return self.render_to_response(self.get_context_data(form=form))
        
        return super(MakePaymentView, self).form_valid(form)


 



class MpesaPaymentView(UserActivityLogMixin, APIView):
    permission_classes = (AllowAny,)
    request_type = ""
    """
    List all snippets, or create a new snippet.
    """
    

    def post(self, request, *args, **kwargs):
        serializer = MpesaSerializer(data=request.data)
        
        """ Check if maintenance mode is True"""
        m_mode = MySettingClass.maintenance_mode()
        if m_mode:
            if self.request_type == "confirmation":
                
                message = '"{}<=>{}<=>{}"'.format('maintenance', 'payment_denied', dict(serializer.initial_data))
                self.request._request.invalid_msg = message
                
                return Response(settings.SAFCOM_CONFIRMATION_FAILURE, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            else:
                
                message = '"{}<=>{}<=>{}"'.format('maintenance', 'payment_denied', dict(serializer.initial_data))
                self.request._request.invalid_msg = message
                
                return Response(settings.SAFCOM_VALIDATION_REJECTED, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        
        """ Check MySetting if payments are allowed"""
        accept_payments = MySettingClass.accept_payments()

        if not accept_payments:
            
            if self.request_type == "confirmation":
                
                message = '"{}<=>{}<=>{}"'.format('payment_not_allowed', 'payment_denied', dict(serializer.initial_data))
                self.request._request.invalid_msg = message
                
                
                return Response(settings.SAFCOM_CONFIRMATION_FAILURE, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            else:
                
                message = '"{}<=>{}<=>{}"'.format('payment_not_allowed', 'payment_denied', dict(serializer.initial_data))
                self.request._request.invalid_msg = message
                
                return Response(settings.SAFCOM_VALIDATION_REJECTED, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        
        if serializer.is_valid():
            
            
            if serializer.validated_data['BusinessShortCode'] == settings.MPESA_BUSINESS_SHORTCODE:
                correct_business_shortcode = True
            else:
                correct_business_shortcode = False
                
                
            phone = serializer.validated_data['MSISDN']
            if validate_safaricom_number(phone):
                correct_phone = True
            else:
                correct_phone = False
            
      
            
            complete_payment_info = {"payment_method": "mpesa",
                                     "request_type": self.request_type,
                                     "payment_info": serializer.validated_data}
        
            if correct_business_shortcode and correct_phone:
                payment_accepted, error_result = AcceptPayment(**complete_payment_info).accept_payments()
            else:
                payment_accepted, error_result = False, False
            

            if payment_accepted:
                
                if self.request_type == "confirmation":
                    
                    return Response(settings.SAFCOM_CONFIRMATION_SUCCESS, status=status.HTTP_200_OK)
                else:
                    return Response(settings.SAFCOM_VALIDATION_ACCEPTED, status=status.HTTP_200_OK)
                    
            else:
                
                if self.request_type == "confirmation":
                    
                    message = '"{}<=>{}<=>{}"'.format('payment_invalid', error_result, dict(serializer.validated_data))
                    self.request._request.payment_invalid_msg = message
                    
                    return Response(settings.SAFCOM_CONFIRMATION_FAILURE, status=status.HTTP_200_OK)
                else:

                    message = '"{}<=>{}<=>{}"'.format('payment_invalid', error_result, dict(serializer.validated_data))
                    self.request._request.payment_invalid_msg = message
                    
                    return Response(settings.SAFCOM_VALIDATION_REJECTED, status=status.HTTP_200_OK)
            
        else:

            
            message = '"{}<=>form_invalid{}<=>{}"'.format('payment_invalid', dict(serializer.errors), dict(serializer.data))
            self.request._request.payment_invalid_msg= message

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    