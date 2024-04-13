from rest_framework import generics
from rest_framework import permissions
from rest_framework.exceptions import Throttled
from rest_framework.response import Response
from rest_framework import status

from api.serializers import InvoiceListSerializer, InvoiceViewSerializer
from api.utils.api_filters import InvoiceFilter
from api.utils.api_web_pagination import InvoiceResultsSetPagination 

from api.utils.permission_helpers.api_view_permissions import IsTopUserPermission
from profiles.models import Customer
from sales.models import Invoice

class InvoiceIndexView(generics.ListCreateAPIView):
    queryset = Invoice.objects.all().select_related(
        'user', 'profile', 'payment_type'
    )
    serializer_class = InvoiceListSerializer
    permission_classes = (permissions.IsAuthenticated, IsTopUserPermission)
    pagination_class = InvoiceResultsSetPagination
    filterset_class=InvoiceFilter

    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(InvoiceIndexView, self).get_queryset()
    
        queryset = queryset.filter(profile__user__email=self.request.user)
        queryset = queryset.order_by('-id') 

        return queryset

    def post(self, request, *args, **kwargs):

        # if api_throttled is in kwargs, throttle the view 
        if kwargs.get('request_throttled', None):
            response = self.handle_exception(Throttled(1))
            self.response = self.finalize_response(request, response, *args, **kwargs)
            
            return self.response

        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():

            self.profile = self.get_profile()

            try:
                self.customer = Customer.objects.get(
                    profile=self.profile, 
                    reg_no=serializer.validated_data['customer_reg_no'] 
                ) 

            except: # pylint: disable=bare-except
                return Response(
                    {'non_field_errors': 'Choose a correct customer'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):

        self.create_invoice(serializer)
        
        # try:
        #     return self.create_invoice(serializer)
        # except: # pylint: disable=bare-except
        #     """ log here """
        #     return 0
            
    def create_invoice(self, serializer):

        local_reg_no = serializer.validated_data['local_reg_no']

class InvoiceView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Invoice.objects.all().select_related(
        'user', 'profile', 'payment_type'
    )
    serializer_class = InvoiceViewSerializer
    permission_classes = (permissions.IsAuthenticated, IsTopUserPermission)
    lookup_field = 'reg_no'
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her object
        """
        queryset = super(InvoiceView, self).get_queryset()
        
        queryset = queryset.filter(
                store__profile__user__email=self.request.user, 
                reg_no=self.kwargs['reg_no']
            )

        return queryset 