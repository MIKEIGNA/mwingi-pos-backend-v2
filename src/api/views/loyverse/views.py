from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from accounts.tasks import (
    update_receipts_task,
    update_products_task,
    update_customers_task,
    update_taxes_task,
) 

from api.serializers import (
    LoyverseWebhookReceiptUpdateSerializer,
    LoyverseWebhookProductUpdateSerializer,
    LoyverseWebhookCustomerUpdateSerializer,
    LoyverseWebhookTaxUpdateSerializer
)
from api.serializers.loyverse.loyverse_webhook_serializers import LoyverseAppDataUpdateSerializer


from core.logger_manager import LoggerManager
from loyverse.models import LoyverseAppData
from profiles.models import Profile

class LoyverseWebhookReceiptUpdateView(APIView):
    permission_classes = ()

    def post(self, request, *args, **kwargs):

        serializer = LoyverseWebhookReceiptUpdateSerializer(
            data=request.data
        )
 
        if serializer.is_valid():
            payload = request.data['receipts']

            user_email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT

            if settings.TESTING_MODE:
                # Calls the task as a normal function
                update_receipts_task(
                    user_email=user_email,
                    receipts=payload
                )

            else:
                # Calls the task as a background task
                update_receipts_task.delay(
                    user_email=user_email,
                    receipts=payload
                )
        else:
            LoggerManager.log_critical_error(additional_message=serializer.errors)
    
        return Response(status=status.HTTP_200_OK)    
    


class LoyverseWebhookProductUpdateView(APIView):
    permission_classes = ()

    def post(self, request, *args, **kwargs):

        serializer = LoyverseWebhookProductUpdateSerializer(
            data=request.data
        )
 
        if serializer.is_valid():
            payload = request.data['products']

            profile = Profile.objects.get(user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT)

            if settings.TESTING_MODE:
                # Calls the task as a normal function
                update_products_task(
                    profile=profile, 
                    products=payload
                )

            else:
                # Calls the task as a background task
                update_products_task.delay(
                    profile=profile, 
                    products=payload
                )
        else:
            LoggerManager.log_critical_error(additional_message=serializer.errors)
    
        return Response(status=status.HTTP_200_OK)  
    

class LoyverseWebhookCustomerUpdateView(APIView):
    permission_classes = ()

    def post(self, request, *args, **kwargs):

        serializer = LoyverseWebhookCustomerUpdateSerializer(
            data=request.data
        )
 
        if serializer.is_valid():
            payload = request.data['customers']

            profile = Profile.objects.get(user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT)

            if settings.TESTING_MODE:
                # Calls the task as a normal function
                update_customers_task(
                    profile=profile, 
                    customers=payload
                )

            else:
                # Calls the task as a background task
                update_customers_task.delay(
                    profile=profile, 
                    customers=payload
                )
        else:
            LoggerManager.log_critical_error(additional_message=serializer.errors)
    
        return Response(status=status.HTTP_200_OK) 
    
class LoyverseWebhookTaxUpdateView(APIView):
    permission_classes = ()

    def post(self, request, *args, **kwargs):

        serializer = LoyverseWebhookTaxUpdateSerializer(
            data=request.data
        )
 
        if serializer.is_valid():
            payload = request.data['taxes']

            profile = Profile.objects.get(user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT)

            if settings.TESTING_MODE:
                # Calls the task as a normal function
                update_taxes_task(
                    profile=profile, 
                    taxes=payload
                )

            else:
                # Calls the task as a background task
                update_taxes_task.delay(
                    profile=profile, 
                    taxes=payload
                )
        else:
            LoggerManager.log_critical_error(additional_message=serializer.errors)
    
        return Response(status=status.HTTP_200_OK) 
    
class LoyverseLoyverseAppDataUpdateView(APIView):
    permission_classes = ()

    def post(self, request, *args, **kwargs):

        serializer = LoyverseAppDataUpdateSerializer(data=request.data)
 
        if serializer.is_valid():

            access_token = serializer.validated_data['access_token']
            refresh_token = serializer.validated_data['refresh_token']

            print(f'Access token {access_token}')
            print(f'Refresh token {refresh_token}')

            print(LoyverseAppData.objects.all())

            LoyverseAppData.objects.all().update(
                access_token = access_token, 
                refresh_token = refresh_token
            )


        else:
            LoggerManager.log_critical_error(additional_message=serializer.errors)

        return Response(status=status.HTTP_200_OK) 