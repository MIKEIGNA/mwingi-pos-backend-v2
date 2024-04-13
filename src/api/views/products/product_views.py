from pprint import pprint
import django_filters.rest_framework

from django.conf import settings
from django.http.response import Http404
from django.db.models.query_utils import Q

from rest_framework import filters
from rest_framework import generics
from rest_framework import permissions
from rest_framework.exceptions import Throttled
from rest_framework.response import Response
from rest_framework import status

from api.serializers import (
    LeanProductListSerializer,
    ProductEditSerializer,
    ProductListSerializer,
    ProductAvailableDataViewSerializer,
)

from api.serializers import LeanProductStoreListSerializer
from api.serializers.products.product_serializers import (
    ProductMapEditSerializer, 
    ProductMapListSerializer, 
    ProductTransformMapListSerializer
)
from api.utils.api_product_view_mixin import ApiProductViewMixin
from api.utils.api_view_bundle_formset_utils import ApiWebBundleFormestHelpers
from api.utils.api_view_formset_utils import ApiWebStoreFormestHelpers
from api.utils.api_view_modifier_formset_utils import ApiWebModifierFormestHelpers
from api.utils.api_view_production_formset_utils import ApiWebProductProductionFormestHelpers
from api.utils.api_web_pagination import ProductLeanWebResultsSetPagination, ProductWebResultsSetPagination
from api.utils.permission_helpers.api_view_permissions import CanViewItemsPermission

from firebase.message_sender_product import ProductMessageSender

from core.mixins.log_entry_mixin import UserActivityLogMixin
from core.my_throttle import ratelimit
from core.my_settings import MySettingClass
from core.image_utils import ApiImageUploader, ApiImageVerifier

from inventories.models import StockLevel

from products.models import Product, ProductBundle, ProductProductionMap
from accounts.utils.user_type import TOP_USER
from profiles.models import Profile
from stores.models import Category, Store, Tax

class TpProductAvailableDataView(generics.RetrieveAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProductAvailableDataViewSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_profile(self):
        """
        Returns the top profile
        """
        if self.request.user.user_type == TOP_USER:
            return self.request.user.profile
        
        else:
            return Profile.objects.get(employeeprofile__user=self.request.user)

    def get_queryset(self):
     
        queryset = super(TpProductAvailableDataView, self).get_queryset()

        if self.request.user.user_type == TOP_USER:
            queryset = queryset.filter(user=self.request.user)
        else:
            queryset = queryset.filter(
                user__profile__employeeprofile__user=self.request.user
            )

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
        context = super(TpProductAvailableDataView, self).get_serializer_context()
        
        profile = self.get_profile()

        # Get models
        context['taxes'] = self.get_model_data_list(
            Tax.objects.filter(stores__profile=profile)
        )
        context['categories'] = self.get_model_data_list(
            Category.objects.filter(profile=profile)
        )
        context['stores'] = self.get_store_list(
            Store.objects.filter(profile=profile)
        )

        return context

class TpLeanProductStoreIndexView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = LeanProductStoreListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = ProductLeanWebResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name',]

    def get_queryset(self):
        """
        Make sure only the owner can view his/her store

        Returns all products with track stock excluding vatiant and bundle parents

        """
        queryset = super(TpLeanProductStoreIndexView, self).get_queryset()

        if self.request.user.user_type == TOP_USER:
            queryset = queryset.filter(profile__user=self.request.user)
        else:
            queryset = queryset.filter(
                profile__employeeprofile__user=self.request.user
            )

        queryset = queryset.filter(
            stores__reg_no=self.kwargs['store1_reg_no'],
            variant_count=0,
            is_deleted=False
        ).order_by('name')

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
            stores_reg_nos = {
                'store1_reg_no': self.kwargs['store1_reg_no'],
                'store2_reg_no': self.kwargs['store2_reg_no']
            } 
        )

class TpLeanProductIndexView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = LeanProductListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = ProductLeanWebResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name',]

    def get_queryset(self):
        """
        Make sure only the owner can view his/her store

        Returns all products excluding variant and bundle parents
        """
        queryset = super(TpLeanProductIndexView, self).get_queryset()

        if self.request.user.user_type == TOP_USER:
            queryset = queryset.filter(profile__user=self.request.user)
        else:
            queryset = queryset.filter(
                profile__employeeprofile__user=self.request.user
            )

        queryset = queryset.filter(
            variant_count=0,
            is_deleted=False
        ).order_by('-id')

        return queryset

class TpProductIndexView(UserActivityLogMixin, generics.ListCreateAPIView, ApiProductViewMixin):
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanViewItemsPermission
    )
    pagination_class = ProductWebResultsSetPagination
    filter_backends = [
        filters.SearchFilter, 
        django_filters.rest_framework.DjangoFilterBackend,
        
    ]
    filterset_fields = [
        'stores__reg_no', 
        'category__reg_no', 
        'stocklevel__status',
        'is_bundle',
        'is_transformable'
    ]
    search_fields = ['name',]

    # Used by ApiCropImageMixin
    image_sub_directory = settings.IMAGE_SETTINGS['product_images_dir']

    # Custom fields
    collected_modifiers = []
    profile = None

    def get_profile(self):
        """
        Returns the top profile
        """
        if self.request.user.user_type == TOP_USER:
            return self.request.user.profile
        
        else:
            return Profile.objects.get(employeeprofile__user=self.request.user)
        
    def get(self, request, *args, **kwargs):
        
        self.profile = self.get_profile()
        
        return super(TpProductIndexView, self).get(request, *args, **kwargs)


    def get_queryset(self):
        """
        Make sure only the owner can view his/her store
        """
        queryset = super(TpProductIndexView, self).get_queryset()

        if self.request.user.user_type == TOP_USER:
            queryset = queryset.filter(profile__user=self.request.user)
        else:
            queryset = queryset.filter(
                profile__employeeprofile__user=self.request.user
            )

        queryset = queryset.filter(
            is_variant_child=False,
            is_deleted=False,
        ).order_by('name')

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
            current_user_profile=self.profile,
            store_reg_no= self.request.query_params.get('stores__reg_no', None)
        )

    @ratelimit(
        scope='api_ip', 
        rate=settings.THROTTLE_RATES['api_product_rate'], 
        alt_name='api_product_create'
    )
    def post(self, request, *args, **kwargs):

        # if api_throttled is in kwargs, throttle the view 
        if kwargs.get('request_throttled', None):
            response = self.handle_exception(Throttled(1))
            self.response = self.finalize_response(request, response, *args, **kwargs)
            
            return self.response
        
        allow_product = MySettingClass.allow_new_product()

        if not allow_product: 
            return Response(status=status.HTTP_423_LOCKED)
        
        self.profile = self.get_profile()

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():

            # Confirm if stores belongs to the store
            stores_info = serializer.validated_data['stores_info']

            self.collected_stores = ApiWebStoreFormestHelpers.get_store_sellable_data_for_top_user(
                stores_info=stores_info, 
                profile=self.profile, 
                check_if_dirty=False
            )

            if not self.collected_stores:
                error_data = {'stores_info': "You provided wrong stores."}
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST) 

            # Verify and collect product data
            self.collected_bundle_products = ApiWebStoreFormestHelpers.validate_bundle_info(
                serializer.validated_data['bundles_info'],
                self.profile
            )


            print("Bundles")
            pprint(self.collected_bundle_products)

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

        return self.create_product(serializer)
      
        # try:
        #     return self.create_product(serializer)
        # except Exception as e : # pylint: disable=bare-except
        #     """ log here """
        #     return 0

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


class TpProductEditView(
    UserActivityLogMixin, 
    generics.RetrieveUpdateDestroyAPIView, 
    ApiProductViewMixin 
    ):
    """ This view represents both the IndexView and CreateView for Profile """
    queryset = Product.objects.all()
    serializer_class = ProductEditSerializer
    permission_classes = (permissions.IsAuthenticated, CanViewItemsPermission)
    lookup_field = 'reg_no'

    # Used by ApiCropImageMixin
    image_sub_directory = settings.IMAGE_SETTINGS['product_images_dir']

    # Custom fields
    collected_modifiers = []
    
    @ratelimit(
        scope='api_user', 
        rate=settings.THROTTLE_RATES['api_product_rate'], 
        alt_name='api_product_edit'
    )
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
     
        self.obj = super(TpProductEditView, self).get_object()
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
        context = super(TpProductEditView, self).get_serializer_context()

        # Get taxes
        context['available_taxes'] = self.get_model_data_list(
            Tax.objects.filter(
                stores__profile__user=self.request.user
            )
        )

        # Get categories
        context['available_categories'] = self.get_model_data_list(
            Category.objects.filter(
                profile__user=self.request.user
            )
        ) 
 
        # Get stores
        context['registered_stores'] = self.obj.get_product_view_stock_level_list()
        context['available_stores'] = self.get_store_list(
            Store.objects.filter(
                profile__user=self.request.user,
                is_deleted=False
            )
        )
        
        return context

    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, 
                                **kwargs, 
                                current_user_profile=self.request.user.profile,
                                product_reg_no=self.kwargs['reg_no'])

    def get_queryset(self):
        """
        Make sure only the owner can view his/her store
        """
        queryset = super(TpProductEditView, self).get_queryset()
        queryset = queryset.filter(
            reg_no=self.kwargs['reg_no'],
            is_variant_child=False,
        ).order_by('-id')

        return queryset.filter(profile__user__email=self.request.user)

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

            self.profile = self.request.user.profile
            
            # Confirm if stores belongs to the store
            stores_info = serializer.validated_data['stores_info']

            self.collected_stores = ApiWebStoreFormestHelpers.get_store_sellable_data_for_top_user(
                stores_info, self.profile
            )

            if not self.collected_stores:
                error_data = {'stores_info': "You provided wrong stores."}
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST) 

            # Verify and collect product data
            self.collected_bundle_products = ApiWebStoreFormestHelpers.validate_bundle_info(
                serializer.validated_data['bundles_info'],
                self.profile
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
        Update product tax, category, modifiers and stock level
        """
        # Determine product type
        is_bundle = len(self.collected_bundle_products) > 0

        tax=self.get_tax(self.profile, serializer.validated_data['tax_reg_no'])
        category=self.get_category(
            self.profile, 
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
                profile=self.profile,
                bundles_data=self.collected_bundle_products
            )  
            
        # Update stock levels
        self.update_stock_levels(product, self.collected_stores)

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

    def perform_destroy(self, instance):
        instance.soft_delete()
        instance.send_firebase_delete_message()















class ProductMapIndexView(UserActivityLogMixin, generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductMapListSerializer
    permission_classes = (permissions.IsAuthenticated, CanViewItemsPermission)
    pagination_class = ProductWebResultsSetPagination

    # Custom fields
    profile = None
    product = None

    def get_profile(self):
        """
        Returns the top profile
        """
        if self.request.user.user_type == TOP_USER:
            return self.request.user.profile
        
        else:
            return Profile.objects.get(employeeprofile__user=self.request.user)

    def get_product(self, product_reg_no):

        try:

            if self.request.user.user_type == TOP_USER:
                return Product.objects.get(
                    profile__user=self.request.user,
                    reg_no=product_reg_no
                )
            else:
                return Product.objects.get(
                    profile__employeeprofile__user=self.request.user,
                    reg_no=product_reg_no
                )
        except:
            return None
        
    @ratelimit(
        scope='api_ip', 
        rate=settings.THROTTLE_RATES['api_product_rate'], 
        alt_name='api_product_create'
    )
    def post(self, request, *args, **kwargs):

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

            self.product = self.get_product(serializer.validated_data['reg_no'])
            if not self.product:
                return Response(status=status.HTTP_404_NOT_FOUND)
            
            # Verify and collect product data
            self.collected_bundle_products = ApiWebStoreFormestHelpers.validate_product_map_info(
                serializer.validated_data['map_info'],
                self.get_profile()
            )

            if not type(self.collected_bundle_products) == list:
                error_data = {'non_field_errors': 'Product map error.'}
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST)

        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):

        self.create_bundle_product(
            bundle_data=self.collected_bundle_products
        )

    def create_bundle_product(self, bundle_data):

        bundle_ids = []
        for bundle in bundle_data:
            pb = ProductProductionMap.objects.create(
                product_map=bundle['model'],
                quantity=bundle['quantity']
            )

            bundle_ids.append(pb.id)

        self.product.productions.add(*bundle_ids)

 
class TpProductMapEditView(
    UserActivityLogMixin, 
    generics.RetrieveUpdateDestroyAPIView):
    """ This view represents both the IndexView and CreateView for Profile """
    queryset = Product.objects.all()
    serializer_class = ProductMapEditSerializer
    permission_classes = (permissions.IsAuthenticated, CanViewItemsPermission)
    lookup_field = 'reg_no'

    product = None

    def get_profile(self):
        """
        Returns the top profile
        """
        if self.request.user.user_type == TOP_USER:
            return self.request.user.profile
        
        else:
            return Profile.objects.get(employeeprofile__user=self.request.user)
    
    @ratelimit(
        scope='api_user', 
        rate=settings.THROTTLE_RATES['api_product_rate'], 
        alt_name='api_product_edit'
    )
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
     
        self.obj = super(TpProductMapEditView, self).get_object()
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

    def get_queryset(self):
        """
        Make sure only the owner can view his/her store
        """
        queryset = super(TpProductMapEditView, self).get_queryset()

        if self.request.user.user_type == TOP_USER:
            queryset = queryset.filter(profile__user=self.request.user)
        else:
            queryset = queryset.filter(
                profile__employeeprofile__user=self.request.user
            )

        queryset = queryset.filter(
            reg_no=self.kwargs['reg_no'],
            is_variant_child=False,
        ).order_by('-id')

        return queryset
        
    """
    Update a model instance.
    """
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid(raise_exception=True):

            self.profile = self.get_profile()

            # Verify and collect product data
            self.collected_bundle_products = ApiWebStoreFormestHelpers.validate_product_map_info(
                serializer.validated_data['map_info'],
                self.profile
            )

            if not type(self.collected_bundle_products) == list:
                error_data = {'non_field_errors': 'Product map error.'}
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST)
            
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update(self, serializer): 
        """
        Update product tax, category, modifiers and stock level
        """
        # Adds or removes product maps from the passed model
        ApiWebProductProductionFormestHelpers.validate_product_maps(
            master_product=self.obj,
            profile=self.profile,
            production_data=self.collected_bundle_products
        ) 
        

class ProductTransformMapIndexView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductTransformMapListSerializer
    permission_classes = (permissions.IsAuthenticated, CanViewItemsPermission)
    pagination_class = ProductLeanWebResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name',]

    # Custom fields
    store = None
    profile = None

    def get(self, request, *args, **kwargs):

        if self.request.user.user_type == TOP_USER:
            self.profile=self.request.user.profile
        else:
            self.profile=Profile.objects.get(employeeprofile__user=self.request.user)

        # Verify store
        try:
            self.store = Store.objects.get(reg_no=self.kwargs['store_reg_no'])
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return super(ProductTransformMapIndexView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Make sure only the owner can view his/her store

        Returns all products with track stock excluding vatiant and bundle parents

        """
        queryset = super(ProductTransformMapIndexView, self).get_queryset()
    
        queryset = queryset.filter(
            profile=self.profile,
            stores__reg_no=self.kwargs['store_reg_no'],
        )

        queryset = queryset.filter(
            Q(productions__gte=0) | 
            Q(productproductionmap__isnull=False)
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
            store_model = self.store
        )