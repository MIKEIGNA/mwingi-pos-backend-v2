from products.models import Product, ProductProductionMap

class ApiWebProductProductionFormestHelpers:

    @staticmethod
    def validate_product_maps(master_product, profile, production_data):
        """
        Collects the product maps from the passed data and then updates them
        """
        query = Product.objects.filter(
            productproductionmap__product=master_product
        ).values_list('reg_no')

        saved_production_reg_nos = [x[0] for x in query]

        collected_production_reg_nos = []
        new_production_info = []

        print(production_data)
        for map_info in production_data:

            # This info will be used later to create/delete models
            if not map_info['reg_no'] in saved_production_reg_nos:
                new_production_info.append(map_info)
                continue

            else:
                collected_production_reg_nos.append(map_info['reg_no'])

            if map_info.get('is_dirty', None):

                print(map_info)
                    
                try:

                    # Update product
                    product_map = ProductProductionMap.objects.get(
                        product_map__reg_no=map_info['reg_no'], 
                        product_map__profile=profile
                    )

                    product_map.quantity = map_info['quantity']
                    product_map.is_auto_repackage = map_info['is_auto_repackage']
                    product_map.save()

                except Exception as e: # pylint: disable=bare-except
                    print(e)
                    """
                    Log here
                    """ 
        # Remove unwanted production maps
        ApiWebProductProductionFormestHelpers.remove_production_maps(
            saved_production_reg_nos,
            collected_production_reg_nos
        )

        # Add new production maps
        ApiWebProductProductionFormestHelpers.create_production_maps(
            master_product=master_product,
            product_production_maps=new_production_info
        )

        return True
    
    @staticmethod
    def remove_production_maps(saved_product_maps_reg_nos, collected_product_maps):

        # List to be removed
        list_to_be_removed = []
        for i in range(len(saved_product_maps_reg_nos)):
            if not saved_product_maps_reg_nos[i] in collected_product_maps:
                list_to_be_removed.append(saved_product_maps_reg_nos[i])

        ProductProductionMap.objects.filter(
            product_map__reg_no__in=list_to_be_removed
        ).delete()
 
    @staticmethod
    def create_production_maps(master_product, product_production_maps):
        """
        Creates product production
        """

        map_ids = []
        for map in product_production_maps:
            pb = ProductProductionMap.objects.create(
                product_map=map['model'],
                quantity=map['quantity']
            )

            map_ids.append(pb.id)

        master_product.productions.add(*map_ids)
