from django.conf import settings
from django.http import Http404

from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import Throttled
from api.utils.permission_helpers.api_view_permissions import IsEmployeeUserPermission, ItemPermission

from core.mixins.log_entry_mixin import UserActivityLogMixin
from core.my_settings import MySettingClass
from core.my_throttle import ratelimit
from core.image_utils import ApiImageUploader

from api.utils.api_product_view_mixin import ApiProductViewMixin
from api.utils.api_view_variant_formset_utils import ApiPosVariantsFormestHelpers
from api.utils.api_pagination import ProductPosResultsSetPagination
from api.utils.api_view_modifier_formset_utils import ApiPosModifierFormestHelpers
from api.serializers import (
    PosProductListSerializer,
    PosProductEditSerializer,
    PosProductImageEditSerializer
)
from firebase.message_sender_product import ProductMessageSender

from inventories.models import StockLevel
from products.models import Product
from accounts.utils.user_type import TOP_USER
from profiles.models import EmployeeProfile
from stores.models import Store

class EpProductPosIndexView(UserActivityLogMixin, generics.ListCreateAPIView, ApiProductViewMixin):
    queryset = Product.objects.all()
    serializer_class = PosProductListSerializer
    permission_classes = (
        permissions.IsAuthenticated, 
        ItemPermission, 
        IsEmployeeUserPermission
    )
    pagination_class = ProductPosResultsSetPagination
    lookup_field = 'store_reg_no'

    # Custom fields
    collected_modifiers = []
    top_profile = None

    def verify_user_and_get_top_profile(self):
        """
        Returns True if user is not top user and employee has access
        to store

        Also extracts top_profile from employee profile and stores it globally
        """
        try:
            self.top_profile = EmployeeProfile.objects.get(
                user=self.request.user,
                stores__reg_no=self.kwargs['store_reg_no'],
            ).profile

        except: # pylint: disable=bare-except
            return False

        return True 

    def get(self, request, *args, **kwargs):
        
        # Verify employee
        if not self.verify_user_and_get_top_profile():
            return Response(status=status.HTTP_404_NOT_FOUND)

        return super(EpProductPosIndexView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Make sure only the owner can view his/her store
        """
        queryset = super(EpProductPosIndexView, self).get_queryset()

        non_sellable_stock_reg_nos = StockLevel.objects.filter(
            store__reg_no=self.kwargs['store_reg_no'], 
            is_sellable=False
        ).values_list('product__reg_no', flat=True)

        queryset = queryset.filter(
            stores__reg_no=self.kwargs['store_reg_no'],
            is_variant_child=False,
        ).exclude(
            reg_no__in=non_sellable_stock_reg_nos
        ).order_by('-name').distinct()

        # Used to pass data to pagination
        self.request.data['view_data'] = {
            'store_reg_no': self.kwargs['store_reg_no']
        }

        return queryset.filter(profile=self.top_profile)

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
            current_user_profile=self.top_profile,
            store_reg_no=self.kwargs['store_reg_no']
        )

    @ratelimit(
        scope='api_ip', 
        rate=settings.THROTTLE_RATES['api_product_rate'], 
        alt_name='api_product_create'
    )
    def post(self, request, *args, **kwargs):

        # Verify employee
        if not self.verify_user_and_get_top_profile():
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

            self.store = None

            try:
                self.store = Store.objects.get(
                    profile=self.top_profile, 
                    reg_no=self.kwargs['store_reg_no']
                )
            
                """ Confirm if modifier belongs to the store"""
                modifiers_info = serializer.validated_data['modifiers_info']

                self.collected_modifiers = ApiPosModifierFormestHelpers.validate_pos_modifiers(
                    modifiers_info, self.store,
                )

                if not type(self.collected_modifiers) == list:
                    error_data = {'modifiers_info': "You provided wrong modifiers."}
                    return Response(error_data, status=status.HTTP_400_BAD_REQUEST)             

            except: # pylint: disable=bare-except
                return Response(status=status.HTTP_404_NOT_FOUND)

        return self.create(request, *args, **kwargs)

    """
    Create a model instance.
    """
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Start our stuff here do our stuff here
        reg_no = self.perform_create(serializer)

        json_response = {'reg_no': reg_no}

        headers = self.get_success_headers(serializer.data)
        return Response(json_response, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        
        try:
            return self.create_product(serializer)
        except: # pylint: disable=bare-except
            """ log here """
            return 0

    def create_product(self, serializer):

        tax=self.get_tax(self.top_profile, serializer.validated_data['tax_reg_no'])
        category=self.get_category(
            self.top_profile, 
            serializer.validated_data['category_reg_no']
        )

        product = Product.objects.create(
            profile=self.top_profile,
            tax=tax,
            category=category,
            color_code=serializer.validated_data['color_code'],
            name=serializer.validated_data['name'],
            cost=serializer.validated_data['cost'],
            price=serializer.validated_data['price'],
            sku=serializer.validated_data['sku'],
            barcode=serializer.validated_data['barcode'],
            sold_by_each=serializer.validated_data['sold_by_each'],
            track_stock=serializer.validated_data['track_stock'],
            show_product=serializer.validated_data['show_product'],
            show_image=serializer.validated_data['show_image']
        )
        product.stores.add(self.store)
        product.modifiers.add(*self.collected_modifiers)

        StockLevel.objects.filter(
            product=product, 
            store=self.store
        ).update(
            minimum_stock_level=serializer.validated_data['minimum_stock_level'],
            units=serializer.validated_data['stocks_units']
        )

        # Send firebase update
        ProductMessageSender.send_product_creation_update_to_users(product)

        return product.reg_no


class EpProductPosEditView(
    UserActivityLogMixin, 
    generics.RetrieveUpdateDestroyAPIView, 
    ApiProductViewMixin
    ):
    """ This view represents both the IndexView and CreateView for Profile """
    queryset = Product.objects.all()
    serializer_class = PosProductEditSerializer
    permission_classes = (
        permissions.IsAuthenticated, 
        ItemPermission,
        IsEmployeeUserPermission
    )
    lookup_field = 'reg_no'

    # Custom fields
    collected_modifiers = []
    top_profile = None

    def verify_user_and_get_top_profile(self):
        """
        Returns True if user is not top user and employee has access
        to store

        Also extracts top_profile from employee profile and stores it globally
        """

        # Make sure is not top user
        if self.request.user.user_type == TOP_USER:
            return False

        try:
            self.top_profile = EmployeeProfile.objects.get(
                user=self.request.user,
                stores__reg_no=self.kwargs['store_reg_no'],
            ).profile

        except: # pylint: disable=bare-except
            return False

        return True
    
    @ratelimit(scope='api_user', rate=settings.THROTTLE_RATES['api_product_rate'], alt_name='api_product_edit')
    def put(self, request, *args, **kwargs):

        # Verify employee
        if not self.verify_user_and_get_top_profile():
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        # if api_throttled is in kwargs, throttle the view 
        if kwargs.get('request_throttled', None):
            response = self.handle_exception(Throttled(1))
            self.response = self.finalize_response(request, response, *args, **kwargs)
            
            return self.response
        
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):

        # Verify employee
        if not self.verify_user_and_get_top_profile():
            return Response(status=status.HTTP_404_NOT_FOUND)

        return super(EpProductPosEditView, self).delete(request, *args, **kwargs)

    def get_object(self):

        store_reg_no = self.kwargs['store_reg_no']
        reg_no = self.kwargs['reg_no']

        """ Check if reg_no is too big"""
        if store_reg_no > 6000000000000 or reg_no > 6000000000000:
            raise Http404
     
        self.obj = super(EpProductPosEditView, self).get_object()
        return self.obj

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
            current_user_profile=self.top_profile,
            product_reg_no=self.kwargs['reg_no']
        )

    def get_queryset(self):
        """
        Make sure only the owner can view his/her store
        """
        queryset = super(EpProductPosEditView, self).get_queryset()

        queryset = queryset.filter(
            stores__reg_no=self.kwargs['store_reg_no'],
            reg_no=self.kwargs['reg_no'],
            is_variant_child=False,
        ).order_by('-id')

        return queryset.filter(profile=self.top_profile)

    """
    Update a model instance.
    """
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid(raise_exception=True):

            self.store = None

            try:
                self.store = Store.objects.get(
                    profile=self.top_profile, 
                    reg_no=self.kwargs['store_reg_no']
                )
            
                """ Confirm if modifier belongs to the top user and the store"""
                modifiers_info = serializer.validated_data['modifiers_info']

                self.collected_modifiers = ApiPosModifierFormestHelpers.validate_pos_modifiers(
                    modifiers_info, self.store,
                )

                if not type(self.collected_modifiers) == list:
                    error_data = {'modifiers_info': "You provided wrong modifiers."}
                    return Response(error_data, status=status.HTTP_400_BAD_REQUEST)    


                """ Confirm if variants belongs to the top user and the store"""
                variants_info = serializer.validated_data['variants_info']

                ApiPosVariantsFormestHelpers.validate_pos_variants(
                    variants_info=variants_info,
                    product=self.obj,
                    store=self.store
                )         

            except: # pylint: disable=bare-except
                return Response(status=status.HTTP_404_NOT_FOUND)

        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update(self, serializer): 
        
        tax=self.get_tax(self.top_profile, serializer.validated_data['tax_reg_no'])
        category=self.get_category(
            self.top_profile, 
            serializer.validated_data['category_reg_no']
        )

        """
        Add tax, category, modifiers and update stock level
        """
        serializer.save(
            tax=tax,
            category=category
        )

        product = serializer.instance

        ApiPosModifierFormestHelpers.add_or_remove_modifiers(
            product, 
            self.collected_modifiers
        )

        StockLevel.objects.filter(
            product=product, 
            store=self.store
        ).update(
            minimum_stock_level=serializer.validated_data['minimum_stock_level'],
            units=serializer.validated_data['stocks_units']
        )

        # Send firebase update
        ProductMessageSender.send_product_edit_update_to_users(product)

class EpProductPosImageEditView(
    UserActivityLogMixin, generics.UpdateAPIView, ApiProductViewMixin):
    queryset = Product.objects.all()
    serializer_class = PosProductImageEditSerializer
    permission_classes = (
        permissions.IsAuthenticated,  
        ItemPermission,
        IsEmployeeUserPermission
    )
    lookup_field = 'reg_no'

    # Custom fields
    top_profile = None

    def verify_user_and_get_top_profile(self):
        """
        Returns True if user is not top user and employee has access
        to store

        Also extracts top_profile from employee profile and stores it globally
        """

        # Make sure is not top user
        if self.request.user.user_type == TOP_USER:
            return False

        try:
            self.top_profile = EmployeeProfile.objects.get(
                user=self.request.user,
                stores__reg_no=self.kwargs['store_reg_no'],
            ).profile

        except: # pylint: disable=bare-except
            return False

        return True

    @ratelimit(
        scope='api_user', 
        rate=settings.THROTTLE_RATES['api_product_image_rate'], 
        alt_name='api_product_image'
    )
    def put(self, request, *args, **kwargs):

        # Verify employee
        if not self.verify_user_and_get_top_profile():
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        # if api_throttled is in kwargs, throttle the view 
        if kwargs.get('request_throttled', None):
            response = self.handle_exception(Throttled(1))
            self.response = self.finalize_response(request, response, *args, **kwargs)
            
            return self.response
        
        return self.update(request, *args, **kwargs)

    def get_object(self):

        store_reg_no = self.kwargs['store_reg_no']
        reg_no = self.kwargs['reg_no']

        """ Check if reg_no is too big"""
        if store_reg_no > 6000000000000 or reg_no > 6000000000000:
            raise Http404

        return super(EpProductPosImageEditView, self).get_object()

    def get_queryset(self):
        """
        Make sure only the owner can view his/her store
        """
        queryset = super(EpProductPosImageEditView, self).get_queryset()

        queryset = queryset.filter(
            stores__reg_no=self.kwargs['store_reg_no'],
            reg_no=self.kwargs['reg_no'],
            is_variant_child=False,
        ).order_by('-id')

        return queryset.filter(profile=self.top_profile)

    def update(self, request, *args, **kwargs):
        
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
    
        serializer.is_valid(raise_exception=True)
                
        # ********** Do your stuff here
        
        try:
   
            image = serializer.validated_data['image']
            
            if not image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                
                error_data = {'error': "Allowed image extensions are .jpg, .jpeg and .png"}
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST)
            
        except: # pylint: disable=bare-except
            error_data = {'error': "You did not provide a valid image"}
            
            return Response(error_data, status=status.HTTP_400_BAD_REQUEST)
        
        # ********** Do your stuff here
        
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
            
        return Response(serializer.data)

    def perform_update(self, serializer):

        product = serializer.instance

        # Save image if we have 1
        uploaded_image = serializer.validated_data.get('image', None)

        if uploaded_image:
            ApiImageUploader(
                model = product,
                serializer_image = uploaded_image
            ).save_and_upload()

        # Send firebase update
        ProductMessageSender.send_product_edit_update_to_users(product)


