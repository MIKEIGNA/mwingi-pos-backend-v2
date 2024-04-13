from django.conf import settings
from django.http.response import Http404
import django_filters

from rest_framework import filters
from rest_framework import generics
from rest_framework import permissions
from rest_framework.exceptions import Throttled
from rest_framework.response import Response
from rest_framework import status

from api.serializers import (
    ProductEditSerializer,
    ProductListSerializer,
    
)
from api.serializers.products.product_serializers import (
    LeanProductListSerializer,
    LeanProductStoreListSerializer, 
    ProductAvailableDataViewSerializer
)
from api.utils.api_product_view_mixin import ApiProductViewMixin
from api.utils.api_view_bundle_formset_utils import ApiWebBundleFormestHelpers
from api.utils.api_view_formset_utils import (
    ApiEmployeeStoreFormestHelpers,
    ApiWebEmployeeStoreFormestHelpers, 
)
from api.utils.api_view_modifier_formset_utils import ApiWebModifierFormestHelpers

from api.utils.api_web_pagination import ProductLeanWebResultsSetPagination, ProductWebResultsSetPagination
from api.utils.permission_helpers.api_view_permissions import CanViewItemsPermission, ItemPermission

from firebase.message_sender_product import ProductMessageSender

from core.mixins.log_entry_mixin import UserActivityLogMixin
from core.my_throttle import ratelimit
from core.my_settings import MySettingClass
from core.image_utils import ApiImageUploader, ApiImageVerifier

from inventories.models import StockLevel

from products.models import Modifier, Product, ProductBundle
from accounts.utils.user_type import TOP_USER
from profiles.models import EmployeeProfile
from stores.models import Category, Store, Tax


class EpProductAvailableDataView(generics.RetrieveAPIView):
    queryset = EmployeeProfile.objects.all()
    serializer_class = ProductAvailableDataViewSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
     
        queryset = super(EpProductAvailableDataView, self).get_queryset()
        queryset = queryset.filter(user__email=self.request.user)

        return queryset

    def get_object(self):

        queryset = self.filter_queryset(self.get_queryset())

        # Get the single item from the filtered queryset
        self.obj = generics.get_object_or_404(queryset)

        # May raise a permission denied
        self.check_object_permissions(self.request, self.obj)

        return self.obj

    def get_store_list(self, queryset):
        """
        Returns a list with dicts that have store names and reg_nos
        """
        queryset = queryset.order_by('id')
        stores = [{'name': s.name, 'reg_no': s.reg_no} for s in queryset]

        return stores

    def get_model_data_list(self, queryset):
        """
        Returns a list with dicts that have models names and reg_nos
        """
        queryset = queryset.order_by('id').distinct()
        results = [{'name': s.name, 'reg_no': s.reg_no} for s in queryset]

        return results

    def get_serializer_context(self):
        context = super(EpProductAvailableDataView, self).get_serializer_context()

        # Get models
        context['modifiers'] = self.get_model_data_list(
            Modifier.objects.filter(
                stores__employeeprofile__user=self.request.user
            )
        )
        context['taxes'] = self.get_model_data_list(
            Tax.objects.filter(
                stores__employeeprofile__user=self.request.user
            )
        )
        context['categories'] = self.get_model_data_list(
            Category.objects.filter(
                profile=self.request.user.employeeprofile.profile
            )
        )
        context['stores'] = self.get_store_list(
            Store.objects.filter(employeeprofile__user=self.request.user)
        )

        return context
    

class EpLeanProductStoreIndexView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = LeanProductStoreListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = ProductLeanWebResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name',]

    def get(self, request, *args, **kwargs):
        
        # Make sure its not top user
        if self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return super(EpLeanProductStoreIndexView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Make sure only the owner can view his/her store

        Returns all products with track stock excluding vatiant and bundle parents

        """
        queryset = super(EpLeanProductStoreIndexView, self).get_queryset()
        queryset = queryset.filter(
            stores__reg_no=self.kwargs['store1_reg_no'],
            variant_count=0,
            is_bundle=False,
        ).order_by('id')

        return queryset.filter(stores__employeeprofile__user=self.request.user,)

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
            stores_reg_nos = {
                'store1_reg_no': self.kwargs['store1_reg_no'],
                'store2_reg_no': self.kwargs['store2_reg_no']
            } 
        )
class EpLeanProductIndexView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = LeanProductListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = ProductLeanWebResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name',]

    def get(self, request, *args, **kwargs):
        
        # Make sure its not top user
        if self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return super(EpLeanProductIndexView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Make sure only the owner can view his/her store

        Returns all products excluding variant and bundle parents

        """
        queryset = super(EpLeanProductIndexView, self).get_queryset()
        queryset = queryset.filter(
            stores__employeeprofile__user=self.request.user,
            variant_count=0,
            is_bundle=False,
        ).order_by('-id')

        return queryset

class EpProductIndexView(UserActivityLogMixin, generics.ListCreateAPIView, ApiProductViewMixin):
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer
    permission_classes = (
        permissions.IsAuthenticated, 
        ItemPermission,
        CanViewItemsPermission
    )
    pagination_class = ProductWebResultsSetPagination
    filter_backends = [
        filters.SearchFilter, 
        django_filters.rest_framework.DjangoFilterBackend
    ]
    filterset_fields = ['stores__reg_no', 'category__reg_no', 'stocklevel__status']
    search_fields = ['name',]

    # Used by ApiCropImageMixin
    image_sub_directory = settings.IMAGE_SETTINGS['product_images_dir']

    # Custom fields
    collected_modifiers = []
    profile = None

    def get(self, request, *args, **kwargs):
        
        # Make sure its not top user
        if self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return super(EpProductIndexView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Make sure only the owner can view his/her store
        """
        queryset = super(EpProductIndexView, self).get_queryset()

        queryset = queryset.filter(
            stores__employeeprofile__user=self.request.user,
            is_variant_child=False
        ).distinct()
        queryset = queryset.order_by('name')

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
            current_user_profile=self.request.user.employeeprofile.profile,
            store_reg_no= self.request.query_params.get('stores__reg_no', None)
        )

    @ratelimit(
        scope='api_ip', 
        rate=settings.THROTTLE_RATES['api_product_rate'], 
        alt_name='api_product_create'
    )
    def post(self, request, *args, **kwargs):

        # Make sure its not top user
        if self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        # if api_throttled is in kwargs, throttle the view 
        if kwargs.get('request_throttled', None):
            response = self.handle_exception(Throttled(1))
            self.response = self.finalize_response(request, response, *args, **kwargs)
            
            return self.response
        
        allow_product = MySettingClass.allow_new_product()

        if not allow_product: 
            return Response(status=status.HTTP_423_LOCKED)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():

            self.profile = self.request.user.employeeprofile.profile
            
            # Confirm if stores belongs to the store
            stores_info = serializer.validated_data['stores_info']

            # Confirm if store belongs to the employee user
            self.employee_profile = EmployeeProfile.objects.get(user=self.request.user)

            self.collected_stores = ApiWebEmployeeStoreFormestHelpers.get_store_sellable_data_for_employee(
                stores_info=stores_info, 
                employee_profile=self.employee_profile, 
                check_if_dirty=False
            )

            if not self.collected_stores:
                error_data = {'stores_info': "You provided wrong stores."}
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST) 

            # Verify and collect product data
            self.collected_bundle_products = ApiEmployeeStoreFormestHelpers.validate_bundle_info(
                serializer.validated_data['bundles_info'],
                self.employee_profile
            )

            if not type(self.collected_bundle_products) == list:
                error_data = {'non_field_errors': 'Bundle error.'}
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST)

        return self.create(request, *args, **kwargs)

    """
    Create a model instance.
    """
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        #  Skip this op if new image has not been passed
        uploaded_image = serializer.validated_data.get('uploaded_image', None)
        if uploaded_image:

            # Verifies an image
            image_error_response = ApiImageVerifier.verify_image(uploaded_image)

            # Return image error if we have any
            if image_error_response: return image_error_response
        
        # Start our stuff here do our stuff here
        reg_no = self.perform_create(serializer)

        json_response = {'reg_no': reg_no}

        headers = self.get_success_headers(serializer.data)
        return Response(json_response, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
      
        # try:
        #     return self.create_product(serializer)
        # except: # pylint: disable=bare-except
        #     """ log here """
        #     return 0

        return self.create_product(serializer)

    def create_bundle_product(self, serializer, category, bundle_data):

        product = Product.objects.create(
            profile=self.profile,
            category=category,
            color_code=serializer.validated_data['color_code'],
            name=serializer.validated_data['name'],
            cost=0, # Since cost cannot be null
            price=serializer.validated_data['price'],
            sku=serializer.validated_data['sku'],
            barcode=serializer.validated_data['barcode'],
            show_image=serializer.validated_data['show_image']
        )
        
        bundle_ids = []
        for bundle in bundle_data:
            pb = ProductBundle.objects.create(
                product_bundle=bundle['model'],
                quantity=bundle['quantity']
            )

            bundle_ids.append(pb.id)

        product.bundles.add(*bundle_ids)

        return product

    def create_normal_product(self, serializer, tax, category):

        product = Product.objects.create(
            profile=self.profile,
            tax=tax,
            category=category,
            color_code=serializer.validated_data['color_code'],
            name=serializer.validated_data['name'],
            cost=serializer.validated_data['cost'],
            price=serializer.validated_data['price'],
            sku=serializer.validated_data['sku'],
            barcode=serializer.validated_data['barcode'],
            sold_by_each=serializer.validated_data['sold_by_each'],
            show_image=serializer.validated_data['show_image']
        )

        return product

    def create_product(self, serializer):

        # Determine product type
        is_bundle = len(self.collected_bundle_products) > 0

        tax=self.get_tax(
            self.profile, 
            serializer.validated_data.get('tax_reg_no', 0)
        )
        category=self.get_category(
            self.profile, 
            serializer.validated_data.get('category_reg_no', 0)
        )

        if is_bundle:
            product = self.create_bundle_product(
                serializer=serializer, 
                category=category,
                bundle_data=self.collected_bundle_products
            )
        else:
            product = self.create_normal_product(
                serializer=serializer, tax=tax, category=category
            )

        # Save image if we have it
        self.save_image(product, serializer)

        stores_ids = Store.objects.filter(profile=product.profile).values_list(
            'id', flat=True
        )

        product.stores.add(*stores_ids)

        if not is_bundle:
            # Create stock levels
            self.update_stock_levels(
                product,
                self.collected_stores
            )

        return product.reg_no

    def save_image(self, model, serializer):
        
        # Save image if we have 1
        uploaded_image = serializer.validated_data.get('uploaded_image', None)

        if uploaded_image:
            ApiImageUploader(
                model = model,
                serializer_image = uploaded_image
            ).save_and_upload()

    def update_stock_levels(self, product, stores):
        """
        Creates product stock levels
        Args:
            product - Product for the stock levels
            stores - A list of dicts with stock level data
                   Eg [
                        {
                            'store_model': 1, 
                            'is_sellable': True
                        }, 
                        {
                            'store_model': 2, 
                            'is_sellable': True
                        }
                    ]
        """
        # Collect the lines that should be edited and ignore the others
        for line in stores:

            if line['is_sellable']:
                StockLevel.objects.filter(  
                    product=product,
                    store=line['store_model']
                ).update(
                    price=line['price'],
                    is_sellable=True
                )

            else:
                StockLevel.objects.filter(  
                    product=product,
                    store=line['store_model']
                ).update(
                    price=line['price'],
                    is_sellable=False
                )

        # Send firebase update
        ProductMessageSender.send_product_creation_update_to_users(product)

  
class EpProductEditView(
    UserActivityLogMixin, 
    generics.RetrieveUpdateDestroyAPIView, 
    ApiProductViewMixin
    ):
    """ This view represents both the IndexView and CreateView for Profile """
    queryset = Product.objects.all()
    serializer_class = ProductEditSerializer
    permission_classes = (
        permissions.IsAuthenticated, 
        ItemPermission,
        CanViewItemsPermission
    )
    lookup_field = 'reg_no'

    # Used by ApiCropImageMixin
    image_sub_directory = settings.IMAGE_SETTINGS['product_images_dir']

    # Custom fields
    collected_modifiers = []
    
    @ratelimit(
        scope='api_user', 
        rate=settings.THROTTLE_RATES['api_product_rate'], 
        alt_name='api_product_edit')
    def put(self, request, *args, **kwargs):
        
        # if api_throttled is in kwargs, throttle the view 
        if kwargs.get('request_throttled', None):
            response = self.handle_exception(Throttled(1))
            self.response = self.finalize_response(request, response, *args, **kwargs)
            
            return self.response
        
        return self.update(request, *args, **kwargs)

    def get_object(self):

        reg_no = self.kwargs['reg_no']

        """ Check if reg_no is too big"""
        if reg_no > 6000000000000:
            raise Http404
     
        self.obj = super(EpProductEditView, self).get_object()
        return self.obj

    def get_store_list(self, queryset):
        """
        Returns a list with dicts that have store names and reg_nos
        """
        queryset = queryset.order_by('name')
        stores = [{'name': s.name, 'reg_no': s.reg_no} for s in queryset]

        return stores

    def get_model_data_list(self, queryset):
        """
        Returns a list with dicts that have models names and reg_nos
        """
        queryset = queryset.order_by('name').distinct()
        results = [{'name': s.name, 'reg_no': s.reg_no} for s in queryset]

        return results

    def get_serializer_context(self):
        context = super(EpProductEditView, self).get_serializer_context()

        # Get modifies
        context['registered_modifiers'] = self.get_model_data_list(
            self.obj.modifiers.all()
        )
        context['available_modifiers'] = self.get_model_data_list(
            Modifier.objects.filter(
                stores__employeeprofile__user=self.request.user
            )
        )

        context['available_taxes'] = self.get_model_data_list(
            Tax.objects.filter(
                stores__employeeprofile__user=self.request.user
            )
        )
        context['available_categories'] = self.get_model_data_list(
            Category.objects.filter(
                profile=self.request.user.employeeprofile.profile
            )
        )
        
        # Get stores
        context['available_stores'] = self.get_store_list(
            Store.objects.filter(
                employeeprofile__user=self.request.user,
                is_deleted=False
            )
        )
        context['registered_stores'] = self.obj.get_product_view_stock_level_list(
            self.request.user.employeeprofile
        )
        
        return context

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
            current_user_profile=self.request.user.employeeprofile.profile,
            product_reg_no=self.kwargs['reg_no'],
            current_employee_profile=self.request.user.employeeprofile
        )

    def get_queryset(self):
        """
        Make sure only the owner can view his/her store
        """
        queryset = super(EpProductEditView, self).get_queryset()
        queryset = queryset.filter(
            stores__employeeprofile__user=self.request.user,
            reg_no=self.kwargs['reg_no'],
            is_variant_child=False,
        ).order_by('-id')

        # Use distinct to prevent unwanted dupblicates when using many to many
        queryset = queryset.distinct()

        return queryset

    """
    Update a model instance.
    """
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid(raise_exception=True):

            #  Skip this op if new image has not been passed
            uploaded_image = serializer.validated_data.get('uploaded_image', None)
            if uploaded_image:

                # Verifies an image
                image_error_response = ApiImageVerifier.verify_image(uploaded_image)

                # Return image error if we have any
                if image_error_response: return image_error_response

            # Confirm if stores belongs to the store
            stores_info = serializer.validated_data['stores_info']

            # Confirm if store belongs to the employee user
            self.employee_profile = EmployeeProfile.objects.get(user=self.request.user)

            self.collected_stores = ApiWebEmployeeStoreFormestHelpers.get_store_sellable_data_for_employee(
                stores_info=stores_info, 
                employee_profile=self.employee_profile
            )
            
            if not self.collected_stores:
                error_data = {'stores_info': "You provided wrong stores."}
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST) 


            # Verify and collect product data
            self.collected_bundle_products = ApiEmployeeStoreFormestHelpers.validate_bundle_info(
                serializer.validated_data['bundles_info'],
                self.employee_profile
            )

            if not type(self.collected_bundle_products) == list:
                error_data = {'non_field_errors': 'Bundle error.'}
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST)
            
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update(self, serializer): 
        """
        Update product tax, category, modifiers, variants and stock level
        """

        profile = self.request.user.employeeprofile.profile

        # Determine product type
        is_bundle = len(self.collected_bundle_products) > 0

        tax=self.get_tax(profile, serializer.validated_data['tax_reg_no'])
        category=self.get_category(
            profile, 
            serializer.validated_data['category_reg_no']
        )

        serializer.save(tax=tax,category=category)

        product = serializer.instance

        # Save image if we have it
        self.save_image(product, serializer)

        # Adds or removes modifiers from the passed model
        ApiWebModifierFormestHelpers.add_or_remove_modifiers(
            product, 
            self.collected_modifiers
        )
      
        # Adds or removes bundles from the passed model
        if is_bundle:
            ApiWebBundleFormestHelpers.validate_bundles(
                master_product=self.obj,
                profile=profile,
                bundles_data=self.collected_bundle_products
            ) 

        # Update stock levels
        self.update_stock_levels(product, self.collected_stores)

    def update_stock_levels(self, product, stores):
        """
        Updates product stock levels
        Args:
            product - Product for the stock levels
            stores - A list of dicts with stock level data
                   Eg [{
                            'store_model': store,
                            'in_stock': info['in_stock'],
                            'minimum_stock_level': info['minimum_stock_level']
                        }]
        """
        # Collect the lines that should be edited and ignore the others
        for line in stores:
            if not line['is_dirty']:
                continue

            if line['is_sellable']:
                StockLevel.objects.filter(  
                    product=product,
                    store=line['store_model']
                ).update(
                    price=line['price'],
                    is_sellable=True
                )

            else:
                StockLevel.objects.filter(  
                    product=product,
                    store=line['store_model']
                ).update(
                    price=line['price'],
                    is_sellable=False
                )

        # Send firebase update
        ProductMessageSender.send_product_edit_update_to_users(product)

    def save_image(self, model, serializer):
        
        # Save image if we have 1
        uploaded_image = serializer.validated_data.get('uploaded_image', None)

        if uploaded_image:
            ApiImageUploader(
                model = model,
                serializer_image = uploaded_image
            ).save_and_upload()

    def perform_destroy(self, instance):
        instance.soft_delete()
        instance.send_firebase_delete_message()


