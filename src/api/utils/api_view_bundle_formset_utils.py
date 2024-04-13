from products.models import Product, ProductBundle

class ApiWebBundleFormestHelpers:

    @staticmethod
    def validate_bundles(master_product, profile, bundles_data):
        """
        Collects the bundles from the passed data and then updates them
        """
        query = Product.objects.filter(
            productbundle__product=master_product
        ).values_list('reg_no')

        saved_bundles_reg_nos = [x[0] for x in query]


        collected_bundles_reg_nos = []
        new_bundles_info = []
        for bundle_info in bundles_data:

            # This info will be used later to create/delete models
            if not bundle_info['reg_no'] in saved_bundles_reg_nos:
                new_bundles_info.append(bundle_info)
                continue

            else:
                collected_bundles_reg_nos.append(bundle_info['reg_no'])

            if bundle_info.get('is_dirty', None):

                try:

                    # Update product
                    product_bundle = ProductBundle.objects.get(
                        product_bundle__reg_no=bundle_info['reg_no'], 
                        product_bundle__profile=profile
                    )

                    product_bundle.quantity = bundle_info['quantity']
                    product_bundle.save()

                except: # pylint: disable=bare-except
                    """
                    Log here
                    """ 
        # Remove unwanted bundles
        ApiWebBundleFormestHelpers.remove_bundles(
            saved_bundles_reg_nos,
            collected_bundles_reg_nos
        )

        # Add new bundles
        ApiWebBundleFormestHelpers.create_bundles(
            master_product=master_product,
            bundles=new_bundles_info
        )

        return True
    
    @staticmethod
    def remove_bundles(saved_bundles_reg_nos, collected_bundles):

        # List to be removed
        list_to_be_removed = []
        for i in range(len(saved_bundles_reg_nos)):
            if not saved_bundles_reg_nos[i] in collected_bundles:
                list_to_be_removed.append(saved_bundles_reg_nos[i])

        ProductBundle.objects.filter(
            product_bundle__reg_no__in=list_to_be_removed
        ).delete()
 
    @staticmethod
    def create_bundles(master_product, bundles):
        """
        Creates product bundles
        """
        bundle_ids = []
        for bundle in bundles:
            pb = ProductBundle.objects.create(
                product_bundle=bundle['model'],
                quantity=bundle['quantity']
            )

            bundle_ids.append(pb.id)

        master_product.bundles.add(*bundle_ids)
