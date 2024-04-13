from inventories.models import InventoryCountLine
from products.models import Product


class InventoryCountLineFormestHelpers:

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
            # We don't ingore the lines that are dirty because it's difficult to
            # track them in the frontend because the data is dynamic
            
            if line['reg_no'] in reg_nos_to_remove:
                continue

            lines_to_edit.append(line)
            
        # Edit lines
        for info in lines_to_edit:
            try:

                lines = InventoryCountLine.objects.filter(
                    reg_no=info['reg_no'], 
                )

                if lines:
                    line = lines[0]

                    line.expected_stock = info['expected_stock']
                    line.counted_stock = info['counted_stock']
                    line.save()

            except Exception as e: #pylint: disable=bare-except
                print(e)
                # LoggerManager.log_critical_error()
                return False

        # Bulk delete
        if reg_nos_to_remove:
            InventoryCountLine.objects.filter(
                reg_no__in=reg_nos_to_remove
            ).delete()
   
        return True

    @staticmethod
    def lines_to_add(inventory_count, products_to_add):
        """
        Adds new store delivery lines

        Args:
            inventory_count (StoreDeliveryNote): Model that will parent the
            new store delivery line
            lines_to_add (list): Has dicts of product reg_nos that 
            should be added
        """

        for product_data in products_to_add:
            
            try:

                product = Product.objects.get(reg_no=product_data['product_reg_no'])

                InventoryCountLine.objects.create(
                    product=product,
                    inventory_count=inventory_count,
                    expected_stock=product_data['expected_stock'],
                    counted_stock=product_data['counted_stock'],
                )

            except: #pylint: disable=bare-except
                'LoggerManager.log_critical_error()'