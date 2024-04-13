from django.template.loader import render_to_string
from django.core.mail import send_mail

from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import generics
from rest_framework import status

from api.serializers.accounts.email_serializers import ReceiptEmailSerializer
from sales.models import Receipt
from sales.views import ReceiptEmailHelpers


class ReceiptEmailView(generics.GenericAPIView):
    serializer_class = ReceiptEmailSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        receipt = None

        try:
            receipt = Receipt.objects.get(
                reg_no=serializer.validated_data['reg_no']
            )
        except: # pylint: disable=bare-except
            return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)


        # send an e-mail to the user
        context = {}
        context = ReceiptEmailHelpers.populate_context_dict(
            context=context,
            receipt=receipt,
            request_user=self.request.user
        )

        # Create and send email  

        subject = f'Receipt from {receipt.store.name}'
        message = render_to_string('sales/receipt_email_template.html', context)
        # from_email: A string. If None, Django will use the value of the 
        # DEFAULT_FROM_EMAIL setting 
        from_email = None
        recipient_list = [serializer.validated_data['email']]

        send_mail(subject, message, from_email, recipient_list, fail_silently=False,)

        return Response({"detail": "Receip email sent."})