from decimal import Decimal
from pprint import pprint
from django.conf import settings
from django.http.response import Http404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.permissions import AllowAny
from rest_framework import generics
from rest_framework.filters import SearchFilter
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import Throttled
from api.serializers.sales.receipt_pos_serializers import PosReceiptRefundPerLineViewSerializer
from api.utils.api_filters import ReceiptFilter
from api.utils.permission_helpers.api_view_permissions import RefundPermission
from core.logger_manager import LoggerManager

from core.my_throttle import ratelimit

from api.serializers import (
    PosReceiptListSerializer,
    PosReceiptCompletePaymentViewSerializer,
    PosReceiptRefundViewSerializer,
)
from api.utils.api_pagination import (
    LeanResultsSetPagination
)
from products.models import ModifierOption, Product
from profiles.models import Customer

from sales.models import Receipt, ReceiptLine, ReceiptPayment
from accounts.utils.user_type import TOP_USER 
from stores.models import Store, StorePaymentMethod, Tax


class PosReceiptIndexView(generics.ListCreateAPIView):
    queryset = Receipt.objects.all()
    serializer_class = PosReceiptListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LeanResultsSetPagination 
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_class=ReceiptFilter 
    search_fields = ['reg_no__in',]

    # Customer fields
    customer = None
    loyalty_points_amount = Decimal(0.00)
    store_payments = []
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(PosReceiptIndexView, self).get_queryset()

        current_user = self.request.user

        if (current_user.user_type == TOP_USER):
            queryset = queryset.filter(
                store__profile__user__email=current_user,
                store__reg_no=self.kwargs['store_reg_no']
            )
        else:
            queryset = queryset.filter(
                store__employeeprofile__user=current_user,
                store__reg_no=self.kwargs['store_reg_no']
                )
            
        queryset = queryset.order_by('-created_date')

        return queryset

    def get_profile(self):

        if self.request.user.user_type == TOP_USER:
            return self.request.user.profile
        else:
            return self.request.user.employeeprofile.profile
    
    @ratelimit(scope='api_ip', rate=settings.THROTTLE_RATES['api_receipt_rate'], alt_name='api_receipt_create')
    def post(self, request, *args, **kwargs):

        # if api_throttled is in kwargs, throttle the view 
        if kwargs.get('request_throttled', None):
            response = self.handle_exception(Throttled(1))
            self.response = self.finalize_response(request, response, *args, **kwargs)
            
            return self.response

        serializer = self.serializer_class(data=request.data)


        print('****************************************8')
        pprint(request.data)

        if serializer.is_valid():
            self.profile = self.get_profile()
            self.store = None

            try:
                self.store = Store.objects.get(
                    profile=self.profile, 
                    reg_no=self.kwargs['store_reg_no']
                )           

            except: # pylint: disable=bare-except
                return Response(status=status.HTTP_404_NOT_FOUND)

            try:
                self.customer = Customer.objects.get(
                    profile=self.profile, 
                    reg_no=serializer.validated_data['customer_details']['data']['customer_reg_no'] 
                ) 

            except: # pylint: disable=bare-except
                " Do nothing "

            lines = serializer.validated_data['payment_methods']

            self.loyalty_points_amount = Decimal(0.00)
            self.store_payments = []
            for line in lines:

                pay_method = self.store.profile.get_store_payment_method_from_reg_no(
                    line['payment_method_reg_no']
                )

                if pay_method:
                    self.store_payments.append(
                        {
                            'pay_method_model': pay_method,
                            'amount': line['amount']
                        }
                    )

                    if pay_method.payment_type == StorePaymentMethod.POINTS_TYPE:
                        self.loyalty_points_amount += Decimal(line['amount'])

                else:
                    return Response(
                        {'non_field_errors': 'Choose a correct payment option'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )


            if self.loyalty_points_amount > 0:
                if self.customer:

                    loyalty_enabled, customer_is_eligible = self.customer.is_eligible_for_point_payment(
                        self.loyalty_points_amount
                    )

                    if not loyalty_enabled:
                        return Response(
                            {'non_field_errors': 'Point payment is not enabled'}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    elif not customer_is_eligible:
                        return Response(
                            {'non_field_errors': 'Customer does not have enough points'}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )

                else:
                    return Response(
                        {'non_field_errors': 'A valid customer is required for point payment'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

            if serializer.validated_data['transaction_type'] == Receipt.DEBT_TRANS:
                if self.customer:

                    if not self.customer.is_eligible_for_debt(serializer.validated_data['subtotal_amount']):
                        return Response(
                            {'non_field_errors': 'Customer is not qualified for debt'}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )

                else:
                    return Response(
                        {'non_field_errors': 'A valid customer is required for debt payment'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

        return self.create(request, *args, **kwargs)

    def get_customer_details(self, customer_details):

        customer_info = {}

        if customer_details.get('data', None):


            customer_info = {
                'name': customer_details['data']['name'], 
                'reg_no': customer_details['data']['customer_reg_no']
            } 

        return customer_info

    def get_product_details(self, product_details):

        product_model = None
        product_info = {'name': 'Not found', 'reg_no': 0} 

        if product_details.get('data', None):

            try:
                product_model = Product.objects.get(
                    profile=self.profile, 
                    reg_no=product_details['data']['product_reg_no'] 
                ) 

            except: # pylint: disable=bare-except
                " Do nothing "

            product_info = {
                'name': product_details['data']['name'], 
                'reg_no': product_details['data']['product_reg_no']
            } 

        return product_model, product_info

    def get_parent_product(self, reg_no):

        if not reg_no > 0: return None

        try:
            return Product.objects.get(
                profile=self.profile, 
                reg_no=reg_no 
            ) 

        except: # pylint: disable=bare-except
            return None
        
    def get_tax(self, reg_no):

        if not reg_no > 0: return None

        try:
            return Tax.objects.get(profile=self.profile, reg_no=reg_no) 

        except: # pylint: disable=bare-except
            return None

    def get_modifier_options_id(self, modifier_option_reg_nos):

        options = []
        for opt_reg_no in modifier_option_reg_nos:

            try:
                options.append(ModifierOption.objects.get(
                    modifier__profile=self.profile,
                    reg_no=opt_reg_no).id
                )
            except: # pylint: disable=bare-except
                " Do nothing"

        return options

    """
    Create a model instance.
    """
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Start our stuff here do our stuff here
        result = self.perform_create(serializer)

        if result == 0:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        json_response = result

        headers = self.get_success_headers(serializer.data)
        return Response(json_response, status=status.HTTP_201_CREATED, headers=headers)
        
    def perform_create(self, serializer):

        try:
            return self.create_receipt(serializer)
        except: # pylint: disable=bare-except
            LoggerManager.log_critical_error() 
            return 0
            
    def create_receipt(self, serializer):

        local_reg_no = serializer.validated_data['local_reg_no']
        receipt_number = serializer.validated_data['receipt_number']

        receipts = Receipt.objects.filter(
            receipt_number=receipt_number, 
            store=self.store
        )

        if receipts:
            receipt = receipts[0]
            
            # Calling save is very important since it will send a firebase
            # to notify listeners that this model has already been synced
            receipt.save()
            
            return Receipt.get_receipts_data(
                self.store, 
                [receipt.reg_no]
            )

        # Create receipt1
        customer_info = self.get_customer_details(
            serializer.validated_data['customer_details']
        )

        receipt = Receipt.objects.create(
            user=self.request.user,
            store=self.store,
            customer=self.customer,
            customer_info=customer_info,
            discount_amount=serializer.validated_data['discount_amount'],
            tax_amount=serializer.validated_data['tax_amount'],
            given_amount=serializer.validated_data['given_amount'],
            change_amount=serializer.validated_data['change_amount'],
            subtotal_amount=serializer.validated_data['subtotal_amount'],
            total_amount=serializer.validated_data['total_amount'],
            loyalty_points_amount=self.loyalty_points_amount,
            transaction_type=serializer.validated_data['transaction_type'],
            payment_completed=serializer.validated_data['payment_completed'],
            item_count=serializer.validated_data['item_count'],
            local_reg_no=local_reg_no,
            created_date_timestamp=serializer.validated_data['created_date_timestamp'],
            receipt_number=serializer.validated_data['receipt_number'],
            show_discount_breakdown=True
        )

        # Create receipt payment
        self.create_receipt_payments(receipt)

        # Create receipt lines
        self.create_receipt_lines(receipt, serializer)

        try:
            # Update cost
            Receipt.objects.get(pk=receipt.pk).calculate_and_update_total_cost()
        except: # pylint: disable=bare-except
            print("Error updating cost")
            """ Log here """

        return Receipt.get_receipts_data(
            self.store, 
            [receipt.reg_no]
        )

    def create_receipt_payments(self, receipt):

        for line in self.store_payments:

            ReceiptPayment.objects.create(
                receipt=receipt,
                payment_method=line['pay_method_model'],
                amount=line['amount']
            )

    def create_receipt_lines(self, receipt, serializer):
        """
        Creates receiptlines for receipt
        """

        lines = serializer.validated_data['receipt_lines']

        for line in lines:

            product, product_info = self.get_product_details(
                line['product_details']
            )

            options = []

            option_reg_nos = line['modifier_option_reg_nos']

            for opt_reg_no in option_reg_nos:
                options.append(ModifierOption.objects.get(reg_no=opt_reg_no).id)


            price = line['price']
            units = line['units']
            discount_amount = line['discount_amount']

            gross_total_amount = price * units
            total_amount = gross_total_amount - discount_amount


            # total_amount=total_money,
            # gross_total_amount=gross_total_money,

            receiptline = ReceiptLine.objects.create(
                receipt=receipt,
                tax=self.get_tax(line['tax_reg_no']),
                parent_product=self.get_parent_product(line['parent_product_reg_no']),
                product=product,
                product_info=product_info,
                modifier_options_info=line['modifier_options_details'],
                price=line['price'],
                total_amount=total_amount,
                gross_total_amount=gross_total_amount,
                is_variant=line['is_variant'],
                sold_by_each=line['sold_by_each'] ,
                discount_amount=line['discount_amount'],
                units=line['units']
            )

            receiptline.modifier_options.add(
                *self.get_modifier_options_id(line['modifier_option_reg_nos'])
            ) 

        # receipt.send_firebase_update_message(True)

class InternalPosReceiptIndexView(generics.ListCreateAPIView):
    queryset = Receipt.objects.all()
    serializer_class = PosReceiptListSerializer
    permission_classes = ()
    pagination_class = LeanResultsSetPagination 
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_class=ReceiptFilter 
    search_fields = ['reg_no',]


class PosReceiptCompletePaymentView(generics.RetrieveUpdateAPIView):
    queryset = Receipt.objects.all().select_related('user', 'store', 'customer')
    serializer_class = PosReceiptCompletePaymentViewSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = 'reg_no'

    def get_object(self):

        store_reg_no = self.kwargs['store_reg_no']
        reg_no = self.kwargs['reg_no']

        """ Check if reg_no is too big"""
        if store_reg_no > 6000000000000 or reg_no > 6000000000000:
            raise Http404
     
        return super(PosReceiptCompletePaymentView, self).get_object()

    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(PosReceiptCompletePaymentView, self).get_queryset()
        
        queryset = queryset.filter(
            user=self.request.user, 
            store__reg_no=self.kwargs['store_reg_no'],
            reg_no=self.kwargs['reg_no'],
        )
        queryset = queryset.order_by('id')

        return queryset

    def get_profile(self):

        if self.request.user.user_type == TOP_USER:
            return self.request.user.profile
        else:
            return self.request.user.employeeprofile.profile

    def put(self, request, *args, **kwargs):

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():

            receipt = self.get_object()

            profile = self.get_profile()
            customer = receipt.customer

            if serializer.validated_data['transaction_type'] == Receipt.DEBT_TRANS:
                return Response(
                    {'non_field_errors': 'Choose another payment option'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            lines = serializer.validated_data['payment_methods']

            loyalty_points_amount = Decimal(0.00)
            store_payments = []
            for line in lines:

                pay_method = profile.get_store_payment_method_from_reg_no(
                    line['payment_method_reg_no']
                )

                if pay_method:
                    store_payments.append(
                        {
                            'payment_method_reg_no': pay_method.reg_no,
                            'amount': line['amount']
                        }
                    )

                    if pay_method.payment_type == StorePaymentMethod.POINTS_TYPE:
                        loyalty_points_amount += Decimal(line['amount'])

                else:
                    return Response(
                        {'non_field_errors': 'Choose a correct payment option'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

            if loyalty_points_amount > 0:
                if customer:

                    loyalty_enabled, customer_is_eligible = customer.is_eligible_for_point_payment(
                        loyalty_points_amount
                    )

                    if not loyalty_enabled:
                        return Response(
                            {'non_field_errors': 'Point payment is not enabled'}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    elif not customer_is_eligible:
                        return Response(
                            {'non_field_errors': 'Customer does not have enough points'}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )

                else:
                    return Response(
                        {'non_field_errors': 'A valid customer is required for point payment'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

            receipt.perform_credit_payment_completed(store_payments)

        return self.update(request, *args, **kwargs)
 
class PosReceiptRefundView(generics.RetrieveUpdateAPIView):
    queryset = Receipt.objects.all()
    serializer_class = PosReceiptRefundViewSerializer
    permission_classes = (permissions.IsAuthenticated, RefundPermission)
    lookup_field = 'reg_no'

    def get_object(self):

        store_reg_no = self.kwargs['store_reg_no']
        reg_no = self.kwargs['reg_no']

        """ Check if reg_no is too big"""
        if store_reg_no > 6000000000000 or reg_no > 6000000000000:
            raise Http404
     
        return super(PosReceiptRefundView, self).get_object()

    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(PosReceiptRefundView, self).get_queryset()
        
        queryset = queryset.filter(
            user=self.request.user, 
            store__reg_no=self.kwargs['store_reg_no'],
            reg_no=self.kwargs['reg_no'],
        )
        queryset = queryset.order_by('id')

        return queryset

    def perform_update(self, serializer):

        receipt = serializer.instance
        receipt.perform_refund()



class PosReceiptRefundPerLineView(generics.RetrieveUpdateAPIView):
    queryset = Receipt.objects.all()
    serializer_class = PosReceiptRefundPerLineViewSerializer
    permission_classes = (permissions.IsAuthenticated, RefundPermission)
    lookup_field = 'reg_no'

    def get_object(self):

        store_reg_no = self.kwargs['store_reg_no']
        reg_no = self.kwargs['reg_no']

        """ Check if reg_no is too big"""
        if store_reg_no > 6000000000000 or reg_no > 6000000000000:
            raise Http404
     
        return super(PosReceiptRefundPerLineView, self).get_object()

    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(PosReceiptRefundPerLineView, self).get_queryset()

        current_user = self.request.user

        if (current_user.user_type == TOP_USER):
            queryset = queryset.filter(store__profile__user__email=current_user)
        else:
            queryset = queryset.filter(store__employeeprofile__user=current_user)
        
        queryset = queryset.filter(
            store__reg_no=self.kwargs['store_reg_no'],
            reg_no=self.kwargs['reg_no'],
        )
        queryset = queryset.order_by('id')

        return queryset 
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        refund_response = self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(refund_response)

    def perform_update(self, serializer):
   
        receipt_number = serializer.validated_data['receipt_number']
        refund_discount_amount = serializer.validated_data['discount_amount']
        refund_tax_amount = serializer.validated_data['tax_amount']
        refund_subtotal_amount = serializer.validated_data['subtotal_amount']
        refund_total_amount = serializer.validated_data['total_amount']
        refund_item_count = serializer.validated_data['item_count']
        refund_local_reg_no = serializer.validated_data['local_reg_no']
        refund_created_date_timestamp = serializer.validated_data['created_date_timestamp']
        refund_receipt_lines = serializer.validated_data['receipt_lines']

        receipt = serializer.instance

        refund_response = receipt.perform_new_refund(
            discount_amount=refund_discount_amount,
            tax_amount=refund_tax_amount,
            subtotal_amount=refund_subtotal_amount,
            total_amount=refund_total_amount,
            loyalty_points_amount=0,
            item_count=refund_item_count,
            local_reg_no=refund_local_reg_no,
            receipt_number=receipt_number,
            created_date_timestamp=refund_created_date_timestamp,
            receipt_line_data=refund_receipt_lines
        )

        return refund_response



{
    "is_refund": false, 
    "tax_total": "1.38", 
    "items_list": [
        "0022.12.00 MM Nafuu 1kg 1.00 60.000 60.000", 
        "Mara Moja 1.00 10.000 10.000"
    ], 
    "grand_total": "70.00", 
    "invoice_pin": "P051848193C", 
    "customer_pin": "", 
    "invoice_date": "16/04/24", 
    "net_subtotal": "68.62", 
    "sel_currency": "KSH", 
    "customer_exid": "", 
    "invoice_number": "217-32810", 
    "rel_doc_number": ""
}
