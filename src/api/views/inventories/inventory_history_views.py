import csv
from pprint import pprint
from django.http import StreamingHttpResponse
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import generics
from rest_framework import permissions
from rest_framework import filters
from api.serializers.inventories.inventory_history_serializers import InventoryHistoryListSerializer
from api.utils.api_filters import InventoryHistoryFilterFilter
from api.utils.api_web_pagination import InventoryHistorResultsSetPagination, InventoryHistorResultsSetPagination2
from api.utils.permission_helpers.api_view_permissions import CanViewInventoryPermission
from core.time_utils.time_localizers import utc_to_local_datetime_with_format

from inventories.models import InventoryHistory
from accounts.utils.user_type import TOP_USER 

class InventoryHistoryIndexView(generics.ListCreateAPIView):
    queryset = InventoryHistory.objects.all()
    serializer_class = InventoryHistoryListSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanViewInventoryPermission
    )
    pagination_class = InventoryHistorResultsSetPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_class = InventoryHistoryFilterFilter
    search_fields = ['change_source_name',]
    
    def get_queryset(self):
        """ 
        Make sure only the owner can view his/her objects
        """
        queryset = super(InventoryHistoryIndexView, self).get_queryset()

        reason =self.request.GET.get('reason', '')

        # Used to indicate no reason was selected
        if reason == '000':return queryset.none()
        
        if self.request.user.user_type == TOP_USER:
            queryset = queryset.filter(store__profile__user=self.request.user)
        else:
            queryset = queryset.filter(
                store__profile__employeeprofile__user=self.request.user
            )

        queryset = queryset.distinct().order_by('-created_date', '-id')

        return queryset
    
class InventoryHistoryIndexView2(generics.ListCreateAPIView):

    VIEW_TYPE_NORMAL = 'normal'
    VIEW_TYPE_INVENTORY_CSV = 'inventory_csv'

    # Default view type
    VIEW_TYPE = VIEW_TYPE_NORMAL

    queryset = InventoryHistory.objects.all()
    serializer_class = InventoryHistoryListSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanViewInventoryPermission
    )
    pagination_class = InventoryHistorResultsSetPagination2
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_class = InventoryHistoryFilterFilter
    search_fields = ['change_source_name',]

    def get(self, request, *args, **kwargs):

        if self.VIEW_TYPE == self.VIEW_TYPE_INVENTORY_CSV:
            return self.csv_response()

        return self.list(request, *args, **kwargs)
    
    def csv_response(self):

        user_timezone = self.request.user.get_user_timezone()

        data = [
            [
                'Change Date',
                'Sync Date',
                'Product',
                'Store',
                'Employee',
                'Reason',
                'Adjustment',
                'Stock After'
            ]
        ] 

        # Get the already filtered receipts
        queryset = self.filter_queryset(self.get_queryset())

        queryset = queryset.values_list(
            'created_date',
            'sync_date',
            'product_name',
            'store_name',
            'user_name',
            'change_source_desc',
            'change_source_name',
            'adjustment',
            'stock_after'
        )

        content_list = [
            [
                utc_to_local_datetime_with_format(
                    obj[0], 
                    user_timezone
                ), # Change date
                utc_to_local_datetime_with_format(
                    obj[1], 
                    user_timezone
                ), # Sync date
                obj[2], # Product 
                obj[3], # Store
                obj[4], # Employee
                f'{obj[5]} {obj[6]}', # Reason
                obj[7], # Adjustment
                obj[8] # Stock after
            ] for obj in queryset
        ]
        
        data += content_list
        
        class Echo:
            def write(self, value): return value

        echo_buffer = Echo()
        csv_writer = csv.writer(echo_buffer)

        # By using a generator expression to write each row in the queryset
        # python calculates each row as needed, rather than all at once.
        # Note that the generator uses parentheses, instead of square
        # brackets – ( ) instead of [ ].
        rows = (csv_writer.writerow(row) for row in data)

        response = StreamingHttpResponse(rows, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="users.csv"'
        return response
    
    def get_queryset(self):
        """ 
        Make sure only the owner can view his/her objects
        """
        queryset = super(InventoryHistoryIndexView2, self).get_queryset()

        reason =self.request.GET.get('reason', '')

        # Used to indicate no reason was selected
        if reason == '000':return queryset.none()
        
        if self.request.user.user_type == TOP_USER:
            queryset = queryset.filter(store__profile__user=self.request.user)
        else:
            queryset = queryset.filter(
                store__profile__employeeprofile__user=self.request.user
            )

        queryset = queryset.distinct().order_by('-created_date', '-id')

        return queryset
    
    
