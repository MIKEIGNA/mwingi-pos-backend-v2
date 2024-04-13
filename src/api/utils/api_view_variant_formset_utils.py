from api.utils.api_view_formset_utils import ApiWebStoreFormestHelpers
from inventories.models import StockLevel
from products.models import Product, ProductVariant


class ApiPosVariantsFormestHelpers:

    @staticmethod
    def validate_pos_variants(variants_info, product, store):
        """
        Collects the vaiants from the passed data and then updates products variants
        and their individual stock levels

        Parameters:
            variants_info --> A list of variants's reg_no's that should be verified
            store (Store) --> Store used to verify modifiers
        """

        for info in variants_info:
            
            if info.get('is_dirty', None):

                try:
                
                    Product.objects.filter(reg_no=info['reg_no'], stores=store).update(
                        name=info['name'],
                        price=info['price'],
                        cost=info['cost'],
                        sku=info['sku'],
                        barcode=info['barcode'],
                        show_product=info['show_product']
                    )

                    StockLevel.objects.filter(
                        product__reg_no=info['reg_no'], 
                        store=store
                    ).update(
                        minimum_stock_level=info['minimum_stock_level'],
                        units=info['stock_units']
                    )

                except: # pylint: disable=bare-except
                    " Log here"
                    return False
                    
        return True



class ApiWebVariantsFormestHelpers:

    @staticmethod
    def validate_variants(master_product, profile, variant_data):
        """
        Collects the vaiants from the passed data and then updates products variants
        and their individual stock levels

        Parameters:
            variants_info --> A list of variants's reg_no's that should be verified
            store (Store) --> Store used to verify modifiers
        """

        collected_variants_reg_nos = []
        new_variants_info = []
        for variant_info in variant_data:

            # This info will be used later to create/delete models
            if variant_info['reg_no'] == 0:
                new_variants_info.append(variant_info)
                continue

            else:
                collected_variants_reg_nos.append(variant_info['reg_no'])
    
            if variant_info.get('is_dirty', None):

                try:
                
                    # Update product
                    product = Product.objects.get(
                        reg_no=variant_info['reg_no'], 
                        profile=profile
                    )

                    product.name = variant_info['name']
                    product.price = variant_info['price']
                    product.cost = variant_info['cost']
                    product.sku = variant_info['sku']
                    product.barcode = variant_info['barcode']
                    product.save()
                    
                    # First we add or remove stores
                    ApiWebStoreFormestHelpers.add_or_remove_stores(
                        model=product,
                        collected_stores=[v['store_id'] for v in variant_info['stores_info']]
                    )
                    
                    # Update stock levels
                    for info in variant_info['stores_info']:

                        try:
                            stock = StockLevel.objects.get(
                                product__reg_no=variant_info['reg_no'],
                                store=info['store_model']
                            )

                            stock.units = info['in_stock']
                            stock.minimum_stock_level = info['minimum_stock_level']
                            stock.save()

                        except: # pylint: disable=bare-except
                            """
                            Log here
                            """
                except: # pylint: disable=bare-except
                    """
                    Log here
                    """
                    
        # Remove unwanted variants
        ApiWebVariantsFormestHelpers.remove_variants(
            master_product, 
            collected_variants_reg_nos
        )

        # Add new variants
        ApiWebVariantsFormestHelpers.create_variants(
            profile=profile,
            master_product=master_product,
            variants=new_variants_info
        )

        return True

    @staticmethod
    def remove_variants(product, collected_variants):

        query = Product.objects.filter(
            productvariant__product=product
        ).values_list('reg_no')
        
        current_variants = [x[0] for x in query]

        # List to be removed
        list_to_be_removed = []
        for i in range(len(current_variants)):
            if not current_variants[i] in collected_variants:
                list_to_be_removed.append(current_variants[i])

        product_variants = ProductVariant.objects.filter(
            product_variant__reg_no__in=list_to_be_removed
        ).values_list('id')

        product.variants.remove(*product_variants)

        ProductVariant.objects.filter(
            product_variant__reg_no__in=list_to_be_removed
        ).delete()

    @staticmethod
    def create_variants(profile, master_product, variants):
        """
        Creates product variants
        """
        
        for variant in variants:

            collected_stores_ids = []
            variant_stock_level_data = []
            for store_data in variant['stores_info']:
                collected_stores_ids.append(store_data['store_id'])
                variant_stock_level_data.append(
                    {
                        'store_model': store_data['store_model'],
                        'in_stock': store_data['in_stock'],
                        'minimum_stock_level': store_data['minimum_stock_level']
                    }
                )


            product = Product.objects.create(
                profile=profile,
                name=variant['name'],
                price=variant['price'],
                cost=variant['cost'],
                sku=variant['sku'],
                barcode=variant['barcode'],
                is_variant_child=True
            )
            product.stores.add(*collected_stores_ids)

            variant = ProductVariant.objects.create(product_variant=product)

            master_product.variants.add(variant)

            # Create stock levels
            ApiWebVariantsFormestHelpers.create_stock_levels(
                product,
                variant_stock_level_data
            )

    @staticmethod
    def create_stock_levels(product, stores):
        """
        Creates product stock levels
        Args:
            product - Product for the stock levels
            stores - A list of dicts with stock level data
                   Eg [{
                            'store_model': store,
                            'in_stock': info['in_stock'],
                            'minimum_stock_level': info['minimum_stock_level']
                        }]
        """

        for store_detail in stores:

            try:
                
                stock_level = StockLevel.objects.get(
                    product=product, 
                    store=store_detail['store_model']
                )

                stock_level.units = store_detail['in_stock']
                stock_level.minimum_stock_level = store_detail['minimum_stock_level']
                stock_level.save()

            except: # pylint: disable=bare-except
                pass
      

