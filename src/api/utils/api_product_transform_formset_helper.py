from pprint import pprint
from core.logger_manager import LoggerManager
from inventories.models import ProductTransformLine
from products.models import Product


class ProductTransformLineFormestHelpers:

    @staticmethod
    def update_store_delivery_lines(lines_info, lines_to_remove):
        """
        Collects the lines from the passed data and then updates/delete the models
        depending on their flags

        Parameters:
            lines_info --> A list of purchase order line's reg_no's that 
            should be updated
        """

        reg_nos_to_remove = [d['reg_no'] for d in lines_to_remove ]

        # Collect the lines that should be edited and ignore the others
        lines_to_edit = []
        for line in lines_info:
            if line['reg_no'] in reg_nos_to_remove or not line['is_dirty']:
                continue

            lines_to_edit.append(line)

        # Edit lines
        for info in lines_to_edit:
            try:

                pprint(info)

                lines = ProductTransformLine.objects.filter(
                    reg_no=info['reg_no'], 
                )

                if lines:

                    target_product = Product.objects.get(reg_no=info['target_product_reg_no'])

                    line = lines[0]
                    
                    line.target_product = target_product
                    line.quantity = info['quantity']
                    line.added_quantity=info['added_quantity']
                    line.cost = info['cost']
                    line.save()

            except Exception as e: #pylint: disable=bare-except
                # LoggerManager.log_critical_error()
                print(e)
                return False

        # Bulk delete
        if reg_nos_to_remove:
            ProductTransformLine.objects.filter(
                reg_no__in=reg_nos_to_remove
            ).delete()
   
        return True

    @staticmethod
    def lines_to_add(product_transform, products_to_add):
        """
        Adds new store delivery lines

        Args:
            product_transform (StoreDeliveryNote): Model that will parent the
            new store delivery line
            lines_to_add (list): Has dicts of product reg_nos that 
            should be added
        """

        for product_data in products_to_add:
            
            try:

                source_product = Product.objects.filter(
                    reg_no=product_data['source_product_reg_no']
                ).first()
                target_product = Product.objects.filter(
                    reg_no=product_data['target_product_reg_no']
                ).first()

                if not source_product or not target_product:
                    return

                ProductTransformLine.objects.create(
                    product_transform=product_transform,
                    source_product=source_product,
                    target_product=target_product,
                    quantity=product_data['quantity'],
                    added_quantity=product_data['added_quantity'],
                    cost=product_data['cost'],
                )

            except Exception as e: #pylint: disable=bare-except
                
                print(e)
                LoggerManager.log_critical_error()