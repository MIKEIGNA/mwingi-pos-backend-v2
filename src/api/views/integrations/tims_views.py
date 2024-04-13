from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from sales.models import Receipt

from api.serializers import TimsReceiptViewUpdateSerializer

class TimsReceiptUpdateView(APIView):

    permission_classes = (permissions.IsAuthenticated,)

    def update_receipt(self, tims_data):

        receipt_number = tims_data['receipt_number']
        tims_cu_serial_number = tims_data['tims_cu_serial_number']
        tims_cu_invoice_number = tims_data['tims_cu_invoice_number']
        tims_verification_url = tims_data['tims_verification_url']
        tims_description = tims_data['tims_description']

        Receipt.objects.filter(
            receipt_number=receipt_number
        ).update(
            tims_cu_serial_number=tims_cu_serial_number,
            tims_cu_invoice_number=tims_cu_invoice_number,
            tims_verification_url = tims_verification_url,
            tims_description = tims_description,
            tims_success=True
        )

    def post(self, request, *args, **kwargs):

        serializer = TimsReceiptViewUpdateSerializer(data=request.data)

        if  serializer.is_valid():
            for data in serializer.validated_data['tims_data']:
                self.update_receipt(tims_data=data)
                
            return Response(status=status.HTTP_200_OK) 

        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)