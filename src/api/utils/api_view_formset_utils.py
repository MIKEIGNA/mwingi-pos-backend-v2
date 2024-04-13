from pprint import pprint
from clusters.models import StoreCluster
from core.logger_manager import LoggerManager
from inventories.models import StockLevel
from products.models import Product
from stores.models import Store


class ApiStoreFormestHelpers:

    @staticmethod
    def validate_store_reg_nos_for_top_user(stores_info, profile):
        """
        Collects the stores from the passed info and returns true if validation
        is succefful and false otherwise

        Parameters:
            stores_info --> A list of store's reg_no's that should be verified
            profie (Profile) --> Top user's profile used to verify store
        """

        collected_stores = []
        for info in stores_info:
            reg_no = info['reg_no']
            if reg_no:

                try:
                    collected_stores.append(
                        Store.objects.get(profile=profile, reg_no=reg_no).id
                    )
                except:  # pylint: disable=bare-except
                    # Log here
                    return False

        return collected_stores

    @staticmethod
    def add_or_remove_stores(model, collected_stores):
        """
        Adds or removes stores from the passed model

        Parameters:
            model --> A model with a stores field(ManyToMany)
            collected_stores --> A list of stores id from view
        """

        query = model.stores.all().values_list('id')

        current_stores = [x[0] for x in query]

        # List to be added
        list_to_be_added = []
        for i in range(len(collected_stores)):
            if not collected_stores[i] in current_stores:
                list_to_be_added.append(collected_stores[i])

        # List to be removed
        list_to_be_removed = []
        for i in range(len(current_stores)):
            if not current_stores[i] in collected_stores:
                list_to_be_removed.append(current_stores[i])

        model.stores.add(*list_to_be_added)
        model.stores.remove(*list_to_be_removed)


class ApiWebStoreFormestHelpers:

    @staticmethod
    def validate_store_reg_nos_for_top_user(stores_info, profile):
        """
        Collects the stores from the passed info and returns true if validation
        is succefful and false otherwise

        Parameters:
            stores_info --> A list of store's reg_no's that should be verified
            profie (Profile) --> Top user's profile used to verify store
        """

        collected_stores_ids = []
        collected_stores_models = []
        for info in stores_info:
            reg_no = info['reg_no']
            if reg_no:

                try:

                    store = Store.objects.get(profile=profile, reg_no=reg_no)

                    collected_stores_ids.append(store.id)
                    collected_stores_models.append(
                        {
                            'store_model': store,
                            'in_stock': info['in_stock'],
                            'minimum_stock_level': info['minimum_stock_level']
                        }
                    )

                except:  # pylint: disable=bare-except
                    # Log here
                    return False

        return {
            'collected_stores_ids': collected_stores_ids,
            'collected_stores_models': collected_stores_models
        }
    
    # TODO Delete validate_store_reg_nos_for_top_user    
    @staticmethod
    def get_store_sellable_data_for_top_user(stores_info, profile, check_if_dirty=True):
        """
        Collects the stores from the passed info and returns true if validation
        is succefful and false otherwise

        Parameters:
            stores_info --> A list of store's reg_no's that should be verified
            profie (Profile) --> Top user's profile used to verify store
        """
        collected_stores_models = []
        for info in stores_info:
            reg_no = info['reg_no']
            if reg_no:

                try:

                    store = Store.objects.get(profile=profile, reg_no=reg_no).id

                    if check_if_dirty:


                        collected_stores_models.append(
                            {
                                'store_model': store,
                                'is_sellable': info['is_sellable'],
                                'price': info['price'],
                                'is_dirty': info['is_dirty']
                            }
                        )

                    else:
                        collected_stores_models.append(
                            {
                                'store_model': store,
                                'is_sellable': info['is_sellable'],
                                'price': info['price'],
                            }
                        )


                except:  # pylint: disable=bare-except
                    # Log here
                    return False

        return collected_stores_models
        

    @staticmethod
    def validate_variant_data(variants_info, profile):

        # Collect and verify store data
        collected_stores_ids = []
        collected_stores_data = {}
        collected_store_models = []
        for variant in variants_info:
            for info in variant['stores_info']:
                
                reg_no = info['reg_no']

                if not reg_no in collected_stores_data:

                    try:
                        store = Store.objects.get(profile=profile, reg_no=reg_no)
                        store_id = store.id
                        collected_stores_data[reg_no] = {
                            'store_model': store,
                            'store_id': store_id
                        }

                        collected_stores_ids.append(store_id)
                        collected_store_models.append(
                            {
                                'store_model': store,
                                'in_stock': 0,
                                'minimum_stock_level': 0
                            }
                        )

                    except:  # pylint: disable=bare-except
                        # Log here
                        return False

        # Collect variant data
        variant_data = []
        for variant in variants_info:
            
            # 
            new_stores_info = []
            for info in variant['stores_info']:
                new_stores_info.append(
                    {
                        'in_stock': info['in_stock'], 
                        'minimum_stock_level': info['minimum_stock_level'],
                        'store_model': collected_stores_data[info['reg_no']]['store_model'],
                        'store_id': collected_stores_data[info['reg_no']]['store_id']
                    }
                )

            variant_data.append(
                {
                    'name': variant['name'],
                    'price': variant['price'], 
                    'cost': variant['cost'],  
                    'sku': variant['sku'], 
                    'barcode': variant['barcode'],
                    'reg_no': variant.get('reg_no', 0),
                    'stores_info': new_stores_info,
                    'is_dirty': variant.get('is_dirty', True)
                }
            )

        return {
            'collected_stores_ids': collected_stores_ids,
            'collected_store_models': collected_store_models,
            'variant_data': variant_data
        }

    @staticmethod
    def add_or_remove_stores(model, collected_stores):
        """
        Adds or removes stores from the passed model

        Parameters:
            model --> A model with a stores field(ManyToMany)
            collected_stores --> A list of stores id from view
        """

        query = model.stores.all().values_list('id')

        current_stores = [x[0] for x in query]

        # List to be added
        list_to_be_added = []
        for i in range(len(collected_stores)):
            if not collected_stores[i] in current_stores:
                list_to_be_added.append(collected_stores[i])

        
        # TODO  Remove this
        #query = model.stores.all().values_list('id')

        current_stores = [x[0] for x in query]

        # List to be added
        list_to_be_added = []
        for i in range(len(collected_stores)):
            if not collected_stores[i] in current_stores:
                list_to_be_added.append(collected_stores[i])

        # List to be removed
        list_to_be_removed = []
        for i in range(len(current_stores)):
            if not current_stores[i] in collected_stores:
                list_to_be_removed.append(current_stores[i])

        model.stores.add(*list_to_be_added)
        model.stores.remove(*list_to_be_removed)

    @staticmethod
    def add_or_remove_clusters(model, collected_clusters):
        """
        Adds or removes clusters from the passed model

        Parameters:
            model --> A model with a clusters field(ManyToMany)
            collected_clusters --> A list of clusters id from view
        """

        query = model.clusters.all().values_list('id')

        current_clusters = [x[0] for x in query]

        # List to be added
        list_to_be_added = []
        for i in range(len(collected_clusters)):
            if not collected_clusters[i] in current_clusters:
                list_to_be_added.append(collected_clusters[i])

        
        current_clusters = [x[0] for x in query]

        # List to be added
        list_to_be_added = []
        for i in range(len(collected_clusters)):
            if not collected_clusters[i] in current_clusters:
                list_to_be_added.append(collected_clusters[i])

        # List to be removed
        list_to_be_removed = []
        for i in range(len(current_clusters)):
            if not current_clusters[i] in collected_clusters:
                list_to_be_removed.append(current_clusters[i])

        model.clusters.add(*list_to_be_added)
        model.clusters.remove(*list_to_be_removed)

    @staticmethod
    def update_product_sellable_status(product, stores_info):
        """
        Adds or removes stores from the passed model

        Parameters:
            product --> A product model
            stores_info --> A list of stores id from view
        """

        # Collect the lines that should be edited and ignore the others
        lines_to_edit = []
        for line in stores_info:
            if line['is_dirty']:
                continue

            lines_to_edit.append(line)

        # Edit lines
        for info in lines_to_edit:
            try:

                lines = StockLevel.objects.filter(
                    product=product,
                    store__reg_no=info['reg_no'], 
                )

                if lines:
                    line = lines[0]

                    line.quantity = info['quantity']
                    line.purchase_cost = info['purchase_cost']
                    line.save()

            except: #pylint: disable=bare-except
                LoggerManager.log_critical_error()
                return False

        



        # Collect the lines that should be edited and ignore the others
        # lines_to_edit = []
        # for line in collected_stores:
        #     if line['reg_no'] in line['is_dirty']:
        #         continue

        #     lines_to_edit.append(line)

        # # Edit lines
        # for info in lines_to_edit:
        #     try:

        #         lines = StockLevel.objects.filter(
        #             product=model,
        #             reg_no=info['reg_no'], 
        #         )

        #         if lines:
        #             line = lines[0]

        #             line.quantity = info['quantity']
        #             line.purchase_cost = info['purchase_cost']
        #             line.save()

        #     except: #pylint: disable=bare-except
        #         # LoggerManager.log_critical_error()
        #         return False







        # query = model.stores.all().values_list('id')

        # current_stores = [x[0] for x in query]

        # # List to be added
        # list_to_be_added = []
        # for i in range(len(collected_stores)):
        #     if not collected_stores[i] in current_stores:
        #         list_to_be_added.append(collected_stores[i])

        # current_stores = [x[0] for x in query]

        # # List to be added
        # list_to_be_added = []
        # for i in range(len(collected_stores)):
        #     if not collected_stores[i] in current_stores:
        #         list_to_be_added.append(collected_stores[i])

        # # List to be removed
        # list_to_be_removed = []
        # for i in range(len(current_stores)):
        #     if not current_stores[i] in collected_stores:
        #         list_to_be_removed.append(current_stores[i])

        # print('List to be added')
        # print(list_to_be_added)


        # print('list_to_be_removed')
        # print(list_to_be_removed)

        # # model.stores.add(*list_to_be_added)
        # # model.stores.remove(*list_to_be_removed)

        # StockLevel.objects.filter(
        #     product=model, store__id__in=list_to_be_added
        # ).update(is_sellable=True)

        # StockLevel.objects.filter(
        #     product=model, store__id__in=list_to_be_removed
        # ).update(is_sellable=False)

    @staticmethod
    def validate_bundle_info(bundle_lines, profile):

        line_data = []
        
        for line in bundle_lines:

            try:
                product = Product.objects.get(
                    profile=profile, 
                    reg_no=line['reg_no']
                )

                line_data.append(
                    {
                        'model': product,
                        'quantity': line['quantity'],
                        'id': product.id,
                        'reg_no': line['reg_no'],
                        'is_dirty': line['is_dirty']
                    }
                )
            except: # pylint: disable=bare-except
                return None
            
        return line_data
    
    @staticmethod
    def validate_product_map_info(map_lines, profile):

        line_data = []
        
        for line in map_lines:

            try:
                product = Product.objects.get(
                    profile=profile, 
                    reg_no=line['reg_no']
                )

                line_data.append(
                    {
                        'model': product,
                        'quantity': line['quantity'],
                        'id': product.id,
                        'is_auto_repackage': line['is_auto_repackage'],
                        'reg_no': line['reg_no'],
                        'is_dirty': line['is_dirty']
                    }
                )
            except: # pylint: disable=bare-except
                return None
            
        return line_data
    
    # TODO #1 Remove validate_store_reg_nos this once you add permissons for clusters
    @staticmethod
    def validate_store_reg_nos(stores_info):
        """
        Collects the stores from the passed info and returns true if validation
        is succefful and false otherwise

        Parameters:
            stores_info --> A list of store's reg_no's that should be verified
        """
        collected_stores_ids = []
        for info in stores_info:
            reg_no = info['reg_no']
            if reg_no:

                try:

                    store = Store.objects.get(reg_no=reg_no)

                    collected_stores_ids.append(store.id)
                
                except:  # pylint: disable=bare-except
                    # Log here
                    return False

        return {
            'collected_stores_ids': collected_stores_ids,
        }

    @staticmethod
    def validate_cluster_reg_nos(clusters_info):
        """
        Collects the clusters from the passed info and returns true if validation
        is succefful and false otherwise

        Parameters:
            cluster_info --> A list of clsuter's reg_no's that should be verified
        """
        collected_clusters_ids = []
        for info in clusters_info:
            reg_no = info['reg_no']
            if reg_no:

                try:

                    cluster = StoreCluster.objects.get(reg_no=reg_no)

                    collected_clusters_ids.append(cluster.id)
                
                except:  # pylint: disable=bare-except
                    # Log here
                    return False

        return {
            'collected_clusters_ids': collected_clusters_ids,
        }

class ApiEmployeeStoreFormestHelpers:

    @staticmethod
    def validate_store_reg_nos_for_manager_user(stores_info, employee_profile):
        """
        Collects the stores from the passed info and returns true if validation
        is succefful and false otherwise

        Parameters:
            stores_info --> A list of store's reg_no's that should be verified
            profie (Profile) --> Top user's profile used to verify store
        """

        collected_stores = []
        for info in stores_info:
            reg_no = info['reg_no']
            if reg_no:

                try:
                    collected_stores.append(
                        Store.objects.get(
                            employeeprofile=employee_profile, reg_no=reg_no).id
                    )
                except:  # pylint: disable=bare-except
                    # Log here
                    return False

        return collected_stores

    @staticmethod
    def add_or_remove_stores(model, master_employee_profile, collected_stores):
        """
        Adds or removes stores from the passed model

        Parameters:
            model --> A model with a stores field(ManyToMany)
            collected_stores --> A list of stores id from view
        """

        # Current model's stores
        master_query = master_employee_profile.stores.all().values_list('id')
        master_employee_profile_stores = [x[0] for x in master_query]

        # Current model's stores
        query = model.stores.all().values_list('id')
        current_stores = [x[0] for x in query]

        # Create list to be added
        list_to_be_added = []
        for i in range(len(collected_stores)):

            # This makes sure the master profile has access to the stores
            if collected_stores[i] in master_employee_profile_stores:

                # This makes sure we only add stores that are not aleady in the model
                if not collected_stores[i] in current_stores:
                    list_to_be_added.append(collected_stores[i])

        # Create list to be removed
        list_to_be_removed = []
        for i in range(len(current_stores)):

            # This makes sure the master profile has access to the stores
            if current_stores[i] in master_employee_profile_stores:

                # This makes sure we only remove stores that are not aleady in
                # the model
                if not current_stores[i] in collected_stores:
                    list_to_be_removed.append(current_stores[i])

        # Add/remove
        model.stores.add(*list_to_be_added)
        model.stores.remove(*list_to_be_removed)


    @staticmethod
    def validate_bundle_info(bundle_lines, employee_profile):

        line_data = []
        
        for line in bundle_lines:

            try:
                products = Product.objects.filter(
                    stores__employeeprofile=employee_profile,
                    reg_no=line['reg_no']
                ).distinct()

                product = products[0]

                line_data.append(
                    {
                        'model': product,
                        'quantity': line['quantity'],
                        'id': product.id,
                        'reg_no': line['reg_no'],
                        'is_dirty': line['is_dirty']
                    }
                )
            except: # pylint: disable=bare-except
                return None
            
        return line_data

class ApiWebEmployeeStoreFormestHelpers:

    @staticmethod
    def get_store_sellable_data_for_employee(stores_info, employee_profile, check_if_dirty=True):
        """
        Collects the stores from the passed info and returns true if validation
        is succefful and false otherwise

        Parameters:
            stores_info --> A list of store's reg_no's that should be verified
            profie (Profile) --> Top user's profile used to verify store
        """
        collected_stores_models = []
        for info in stores_info:
            reg_no = info['reg_no']
            if reg_no:

                try:

                    store = Store.objects.get(
                        employeeprofile=employee_profile, 
                        reg_no=reg_no
                    ).id

                    if check_if_dirty:


                        collected_stores_models.append(
                            {
                                'store_model': store,
                                'is_sellable': info['is_sellable'],
                                'price': info['price'],
                                'is_dirty': info['is_dirty']
                            }
                        )

                    else:
                        collected_stores_models.append(
                            {
                                'store_model': store,
                                'price': info['price'],
                                'is_sellable': info['is_sellable'],
                            }
                        )

                except: # pylint: disable=bare-except
                    # Log here
                    return False

        return collected_stores_models

    # TODO Delete validate_store_reg_nos_for_employee
    @staticmethod
    def validate_store_reg_nos_for_employee(stores_info, employee_profile):
        """
        Collects the stores from the passed info and returns true if validation
        is succefful and false otherwise

        Parameters:
            stores_info --> A list of store's reg_no's that should be verified
            employee_profie (EmployeeProfile) --> Employee user's profile used to verify store
        """

        collected_stores_ids = []
        collected_stores_models = []
        for info in stores_info:
            reg_no = info['reg_no']
            if reg_no:

                try:

                    store = Store.objects.get(
                        employeeprofile=employee_profile, 
                        reg_no=reg_no
                    )

                    collected_stores_ids.append(store.id)
                    collected_stores_models.append(
                        {
                            'store_model': store,
                            'in_stock': info['in_stock'],
                            'minimum_stock_level': info['minimum_stock_level']
                        }
                    )

                except:  # pylint: disable=bare-except
                    # Log here
                    return False

        return {
            'collected_stores_ids': collected_stores_ids,
            'collected_stores_models': collected_stores_models
        }

    @staticmethod
    def validate_variant_data(variants_info, employee_profile):

        # Collect and verify store data
        collected_stores_ids = []
        collected_stores_data = {}
        collected_store_models = []
        for variant in variants_info:
            for info in variant['stores_info']:
                
                reg_no = info['reg_no']

                if not reg_no in collected_stores_data:

                    try:
                        store = Store.objects.get(employeeprofile=employee_profile, reg_no=reg_no)
                        store_id = store.id
                        collected_stores_data[reg_no] = {
                            'store_model': store,
                            'store_id': store_id
                        }

                        collected_stores_ids.append(store_id)
                        collected_store_models.append(
                            {
                                'store_model': store,
                                'in_stock': 0,
                                'minimum_stock_level': 0
                            }
                        )

                    except:  # pylint: disable=bare-except
                        # Log here
                        return False

        # Collect variant data
        variant_data = []
        for variant in variants_info:
            
            # 
            new_stores_info = []
            for info in variant['stores_info']:
                new_stores_info.append(
                    {
                        'in_stock': info['in_stock'], 
                        'minimum_stock_level': info['minimum_stock_level'],
                        'store_model': collected_stores_data[info['reg_no']]['store_model'],
                        'store_id': collected_stores_data[info['reg_no']]['store_id']
                    }
                )

            variant_data.append(
                {
                    'name': variant['name'],
                    'price': variant['price'], 
                    'cost': variant['cost'],  
                    'sku': variant['sku'], 
                    'barcode': variant['barcode'],
                    'reg_no': variant.get('reg_no', 0),
                    'stores_info': new_stores_info,
                    'is_dirty': variant.get('is_dirty', True)
                }
            )

        return {
            'collected_stores_ids': collected_stores_ids,
            'collected_store_models': collected_store_models,
            'variant_data': variant_data
        }

    @staticmethod
    def add_or_remove_stores(model, collected_stores):
        """
        Adds or removes stores from the passed model

        Parameters:
            model --> A model with a stores field(ManyToMany)
            collected_stores --> A list of stores id from view
        """

        query = model.stores.all().values_list('id')

        current_stores = [x[0] for x in query]

        # List to be added
        list_to_be_added = []
        for i in range(len(collected_stores)):
            if not collected_stores[i] in current_stores:
                list_to_be_added.append(collected_stores[i])

        
        # TODO  Remove this
        #query = model.stores.all().values_list('id')

        current_stores = [x[0] for x in query]

        # List to be added
        list_to_be_added = []
        for i in range(len(collected_stores)):
            if not collected_stores[i] in current_stores:
                list_to_be_added.append(collected_stores[i])

        # List to be removed
        list_to_be_removed = []
        for i in range(len(current_stores)):
            if not current_stores[i] in collected_stores:
                list_to_be_removed.append(current_stores[i])

        model.stores.add(*list_to_be_added)
        model.stores.remove(*list_to_be_removed)
        
