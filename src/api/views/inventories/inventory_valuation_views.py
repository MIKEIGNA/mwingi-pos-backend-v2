import csv
from django.http import StreamingHttpResponse

from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from api.utils.api_filter_helpers import FilterModelsList

from api.utils.api_web_pagination import InventoryValuationResultsSetPagination
from api.serializers import (
    InventoryValuationListSerializer,
    InventoryValuationSerializer
)
from api.utils.permission_helpers.api_view_permissions import CanViewInventoryPermission
from core.time_utils.time_localizers import is_valid_iso_format
from inventories.models.inventory_valuation_models import InventoryValuation

from products.models import Product
from accounts.utils.user_type import TOP_USER
from profiles.models import EmployeeProfile, Profile






class InventoryValuationIndexView(generics.ListAPIView):

    queryset = Product.objects.all()
    serializer_class = InventoryValuationListSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanViewInventoryPermission
    )
    pagination_class = InventoryValuationResultsSetPagination
    filter_fields = {
       'stores__reg_no': ['exact', 'in'],
    }

    def get_queryset(self):
        """
        Make sure only the owner can view his/her store
        """
        queryset = super(InventoryValuationIndexView, self).get_queryset()

        if self.request.user.user_type == TOP_USER:
            queryset = queryset.filter(profile__user=self.request.user)
        else:
            queryset = queryset.filter(
                profile__employeeprofile__user=self.request.user
            )


        queryset = queryset.filter(
            #stores__reg_no=self.kwargs['store1_reg_no'],
            is_variant_child = False,
            # is_bundle=False,
        ).order_by('name')

        # Use distinct to prevent unwanted dupblicates when using many to many
        queryset = queryset.distinct()

        return queryset

    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(
            *args, 
            **kwargs, 
            stores_reg_nos=InventoryValuationResultsSetPagination.get_stores_reg_nos(self.request))

    def get_stores_reg_nos(self):
        """
        Retrieves stores__reg_no__in param from request and the turns the reg nos
        into a list if they are there. If they are not found, None is returned
        """

        reg_nos = self.request.query_params.get('stores__reg_no__in', None)

        if reg_nos:
            # Removes white spaces and splits from commas
            return reg_nos.replace(' ', '').split(',')
        else:
            return None


class InventoryValuationView(generics.RetrieveUpdateAPIView):
    serializer_class = InventoryValuationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    # Custom fields
    VIEW_TYPE_NORMAL = 'normal'

    VIEW_TYPE_COMPREHENSIVE_CSV_REPORT = 'comprehensive_csv_report'
    VIEW_TYPE_SHORT_CSV_REPORT = 'short_csv_report'

    # Default view type
    VIEW_TYPE = VIEW_TYPE_NORMAL

    selected_date = None
    store_reg_no = None
    user_reg_no = None

    is_owner = None

    def verify_dates(self, date_list):
        """
        Returns True if the list is empty or has valid dates. Otherwise False
        is returned 
        """
        for date in date_list:
            if date:
                if not is_valid_iso_format(date):
                    return False

        return True

    def verify_reg_no(self, reg_nos):
        """
        Returns True if the reg_no is empty or is a valid integers. Otherwise False
        is returned 
        """
        if reg_nos:

            reg_no_list = reg_nos.split(',')

            for reg_no in reg_no_list:
   
                if reg_no.isdigit():
                    if int(reg_no) > 6000000000000:
                        return False
                else:
                    return False

        return True

    def get(self, request, *args, **kwargs): 

        self.is_owner = self.request.user.user_type == TOP_USER

        # Retrive and verify date values
        self.selected_date = self.request.GET.get('date', '')
        
        if not self.verify_dates([self.selected_date,]):
            return Response(
                {'date': ['Enter a valid date.']}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Retrive and verify store reg no values
        self.store_reg_no = self.request.GET.get('store_reg_no', '')
    
        if not self.verify_reg_no(self.store_reg_no):
            return Response(
                {'store_reg_no': ['Enter a number.']}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if self.VIEW_TYPE == self.VIEW_TYPE_COMPREHENSIVE_CSV_REPORT :
            return self.comprehensive_csv_per_receipt_response()
        elif self.VIEW_TYPE == self.VIEW_TYPE_SHORT_CSV_REPORT:
            return self.short_csv_per_receipt_response()

        return super(InventoryValuationView, self).get(request, *args, **kwargs)
    
    def short_csv_per_receipt_response(self):

        csv_data = [
            [
                'Product Name', 
                'Total Stock'
            ]]
    
        ######## Filter store 1
        inventory_valuation_data = InventoryValuation.get_inventory_product_data(
            profile=self.get_user_profile(),
            date=self.selected_date,
        )

        store_names = inventory_valuation_data['stores']
        product_data = inventory_valuation_data['product_data']
        product_units_agg_data = inventory_valuation_data['product_units_agg_data']

        for name in store_names:
            csv_data[0].append(name)

        for name, data in product_data.items():
            datarow_data = [
                name,
                product_units_agg_data[name]               
            ]

            for item in data:
                datarow_data.append(item['units'])

            csv_data += [datarow_data]

        return self.return_csv(csv_data, 'inventory_valuation')
    
    def comprehensive_csv_per_receipt_response(self):

        csv_data = [
            [
                'Product Name', 
                'SKU', 
                'Category', 
                'Cost', 
                'Barcode',
                'Total Stock'
            ]]
    
        ######## Filter store 1
        inventory_valuation_data = InventoryValuation.get_inventory_product_data(
            profile=self.get_user_profile(),
            date=self.selected_date,
        )

        store_names = inventory_valuation_data['stores']
        product_data = inventory_valuation_data['product_data']
        product_units_agg_data = inventory_valuation_data['product_units_agg_data']

        for name in store_names:
            csv_data[0].append(f'Is sellable [{name}]')
            csv_data[0].append(f'Price [{name}]')
            csv_data[0].append(f'Units [{name}]')

        for name, data in product_data.items():
            datarow_data = [
                name,
                data[0]['sku'],
                data[0]['category_name'],
                data[0]['cost'],
                data[0]['barcode'],
                product_units_agg_data[name]               
            ]

            for item in data:
                datarow_data.append(item['is_sellable'])
                datarow_data.append(item['price'])
                datarow_data.append(item['units'])

            csv_data += [datarow_data]

        return self.return_csv(csv_data, 'inventory_valuation')
    
    def return_csv(self, csv_data, filename):
        """
        Returns a csv file
        """

        class Echo:
            def write(self, value): return value

        echo_buffer = Echo()
        csv_writer = csv.writer(echo_buffer)

        # By using a generator expression to write each row in the queryset
        # python calculates each row as needed, rather than all at once.
        # Note that the generator uses parentheses, instead of square
        # brackets – ( ) instead of [ ].
        rows = (csv_writer.writerow(row) for row in csv_data)

        response = StreamingHttpResponse(rows, content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'
        return response

    def get_queryset(self):
        """
        Make sure only the owner can view his/her profile 
        """
        if self.is_owner:
            queryset = queryset = Profile.objects.all()
        else:
            queryset = EmployeeProfile.objects.all()

        queryset = queryset.filter(user__email=self.request.user)

        return queryset

    def get_object(self):

        queryset = self.filter_queryset(self.get_queryset())

        # Get the single item from the filtered queryset
        self.obj = generics.get_object_or_404(queryset)

        # May raise a permission denied
        self.check_object_permissions(self.request, self.obj)

        return self.obj
    
    def get_receipt_queryset(self):
        pass

    def get_user_profile(self):
        """
        Returns the user profile
        """

        if self.request.user.user_type == TOP_USER:
            return self.request.user.profile
        else:
            return self.request.user.employeeprofile.profile
    
    def collect_store_reg_nos(self):

        store_reg_nos_list = []
        try:

            store_reg_nos_list = self.request.GET.get(
                'store_reg_no', 
                None
            ).split(',')
            
        except:
            pass

        # Remove empty strings
        store_reg_nos_list = list(filter(None, store_reg_nos_list))

        return store_reg_nos_list
    
    def get_serializer_context(self):
        
        context = super(InventoryValuationView, self).get_serializer_context()
        
        store_reg_nos_list = self.collect_store_reg_nos()
  
        if self.selected_date:

            inventory_valuation_data = InventoryValuation.get_inventory_valuation_data(
                profile=self.get_user_profile(),
                request_user=self.request.user,
                date=self.selected_date,
                stores_reg_nos=store_reg_nos_list
            )

            context['total_inventory_data'] = inventory_valuation_data['total_inventory_data']
            context['product_data'] = inventory_valuation_data['product_data']

        else:
            context['total_inventory_data'] = {}
            context['product_data'] = []

        context['stores'] = FilterModelsList.get_store_list(self.request.user)

        return context