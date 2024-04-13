from firebase.tasks import firebase_multiple_users_messaging_tasks
from firebase.models import FirebaseDevice
from inventories.models import StockLevel

class ProductMessageSender:

    @staticmethod
    def _get_product_map(product):

        stock_levels = StockLevel.objects.filter(product=product).values(
            'is_sellable', 
            'store__reg_no', 
            'product__reg_no'
        ).order_by('id')

        product_map = []
        for s in stock_levels:
            product_map.append(
                {
                    'store_reg_no': s['store__reg_no'],
                    'is_sellable': s['is_sellable']
                }
            )

        return product_map

    @staticmethod
    def send_product_creation_update_to_users(product):
        """
        Sends a newly cretaed product's data to users through firebase

        Args:
            store (Store): The store that will receive the notification
            product (Product): The new product that has been created
        """
        stores_data = ProductMessageSender._get_product_map(product)

        for store_data in stores_data:
            ProductMessageSender.send_product_update_to_users(
                store_data,
                product,
                'create'
            )

    @staticmethod
    def send_product_edit_update_to_users(product):
        """
        Sends a newly edited product's data to users through firebase

        Args:
            store (Store): The store that will receive the notification
            product (Product): The new product that has been created
        """
        stores_data = ProductMessageSender._get_product_map(product)

        for store_data in stores_data:
            ProductMessageSender.send_product_update_to_users(
                store_data,
                product,
               'edit'
            )

    @staticmethod
    def send_product_update_to_users(store_data, product, action_type):
        """
        Sends a newly cretaed product's data to users through firebase

        Args:
            product (Product): The new product that has been created
            action (String): A str describing the action type
        """
        owner_profile = product.profile
        group_id = owner_profile.get_user_group_identification()

        store_reg_no = store_data['store_reg_no']
        is_sellable = store_data['is_sellable']

        tokens = FirebaseDevice.objects.filter(
            store__reg_no=store_reg_no).values_list('token')
          
        if not is_sellable:

            if not action_type == 'create':
                ProductMessageSender.send_product_deletion_update_to_users(
                    product, 
                    tokens
                )
            return
        
        retrieved_tokens = []
        for token in tokens:
            retrieved_tokens.append(token[0])

        relevant_stores = []

        payload = {
            'group_id': group_id,
            'relevant_stores': str(relevant_stores),
            'model': 'product',
            'action_type': action_type,

            'image_url': product.get_image_url(),
            'color_code': product.color_code,
            'name': product.name,
            'cost': str(product.cost),
            'sku': product.sku,
            'barcode': product.barcode,
            'sold_by_each': str(product.sold_by_each),
            'is_bundle': str(product.is_bundle),
            'track_stock': str(product.track_stock),
            'variant_count': str(product.variant_count),
            'show_product': str(product.show_product),
            'show_image': str(product.show_image),
            'reg_no': str(product.reg_no),
            'stock_level': str(product.get_store_stock_level_data(store_reg_no)),
            'store_reg_no': str(store_reg_no),
            'category_data': str(product.get_category_data()),
            'tax_data': str(product.get_tax_data()),
            'modifier_data': str(product.get_modifier_list()),
            'variant_data': str(product.get_variants_data_from_store(store_reg_no)),
        }

        firebase_multiple_users_messaging_tasks(retrieved_tokens, payload)

    @staticmethod
    def send_product_deletion_update_to_users(product, tokens):
        """
        Sends a newly deleted product's data to users through firebase

        Args:
            tokens (FirebaseDevice List): The tokens that will receive the notification
            product (Product): The new product that has been created
        """

        retrieved_tokens = []
        for token in tokens:
            retrieved_tokens.append(token[0])

        relevant_stores = []

        payload = {
            'group_id': '',
            'relevant_stores': str(relevant_stores),
            'model': 'product',
            'action_type': 'delete',

            'reg_no': str(product.reg_no),
        }

        firebase_multiple_users_messaging_tasks(retrieved_tokens, payload)