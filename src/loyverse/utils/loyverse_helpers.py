from pprint import pprint
from firebase.message_sender_product import ProductMessageSender
from inventories.models import StockLevel
from stores.models import Store


class StoreHelpers:

    @staticmethod
    def get_store_local_ids(stores_info):
        """
        Collects the stores from the passed info and returns true if validation
        is succefful and false otherwise

        Parameters:
            stores_info --> A list of loyverse store ids
        """

        collected_stores_ids = []
        for info in stores_info:

            # Only include items that are available for sale
            if not info['available_for_sale']: continue

            store_id = info['store_id']
            if store_id:

                try:

                    # store = Store.objects.get(loyverse_store_id=store_id)

                    collected_stores_ids.append(
                        {
                            'loyverse_store_id': store_id,
                            'price': info['price'],
                            'is_sellable': info['available_for_sale']
                        })

                except Exception as e:  # pylint: disable=bare-except
                    # Log here
                    print(e)
                    return False

        return collected_stores_ids

    @staticmethod
    def add_or_remove_stores(model, collected_store_ids):
        """
        Adds or removes stores from the passed model

        Parameters:
            model --> A model with a stores field(ManyToMany)
            collected_store_ids --> A list of stores id from view
        """
        stock_levels = StockLevel.objects.filter(product=model).values(
            'store__loyverse_store_id',
            'price',
            'is_sellable'
        ) 

        stock_levels_map = {
            str(stock_level['store__loyverse_store_id']): stock_level
            for stock_level in stock_levels
        }

        # Only update stock levels if there are any changes in price or sellability
        for store_data in collected_store_ids:
            store_id = str(store_data['loyverse_store_id'])
            
            if (stock_levels_map[store_id]['is_sellable'] == store_data['is_sellable']) and (stock_levels_map[store_id]['price'] == store_data['price']):
                continue  

            StockLevel.objects.filter(
                product=model,
                store__loyverse_store_id=store_id
            ).update(
                price=store_data['price'],
                is_sellable=store_data['is_sellable'],
            )  

            # Send firebase update
            ProductMessageSender.send_product_edit_update_to_users(model)
            
        return

    @staticmethod
    def get_store_local_ids_and_sellable_data(stores_info):
        """
        Collects the stores from the passed info and returns true if validation
        is succefful and false otherwise

        Parameters:
            stores_info --> A list of loyverse store ids
        """
        stores_data = []
        for info in stores_info:

            store_id = info['store_id']
            if store_id:

                stock_data = {
                    'loyverse_store_id': info['store_id'],
                    'price': info['price'],
                    'is_sellable': info['available_for_sale']
                }
        
                stores_data.append(stock_data)
                        
        return stores_data