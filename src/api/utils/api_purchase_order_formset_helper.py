from inventories.models import PurchaseOrderLine
from products.models import Product


class PurchaseOrderLineFormestHelpers:

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

                lines = PurchaseOrderLine.objects.filter(
                    reg_no=info['reg_no'], 
                )

                if lines:
                    line = lines[0]

                    line.quantity = info['quantity']
                    line.purchase_cost = info['purchase_cost']
                    line.save()

            except: #pylint: disable=bare-except
                # LoggerManager.log_critical_error()
                return False

        # Bulk delete
        if reg_nos_to_remove:
            PurchaseOrderLine.objects.filter(
                reg_no__in=reg_nos_to_remove
            ).delete()
   
        return True

    @staticmethod
    def lines_to_add(purchase_order, products_to_add):
        """
        Adds new store delivery lines

        Args:
            purchase_order (StoreDeliveryNote): Model that will parent the
            new store delivery line
            lines_to_add (list): Has dicts of product reg_nos that 
            should be added
        """

        for product_data in products_to_add:
            
            try:

                product = Product.objects.get(reg_no=product_data['product_reg_no'])

                PurchaseOrderLine.objects.create(
                    product=product,
                    purchase_order=purchase_order,
                    quantity=product_data['quantity'],
                    purchase_cost=product_data['purchase_cost'],
                )

            except: #pylint: disable=bare-except
                'LoggerManager.log_critical_error()'