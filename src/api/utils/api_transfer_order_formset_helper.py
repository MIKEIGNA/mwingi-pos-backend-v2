from inventories.models import TransferOrderLine
from products.models import Product


class TransferOrderLineFormestHelpers:

    @staticmethod
    def update_store_delivery_lines(lines_info, lines_to_remove):
        """
        Collects the lines from the passed data and then updates/delete the models
        depending on their flags

        Parameters:
            lines_info --> A list of transfer order line's reg_no's that 
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

                lines = TransferOrderLine.objects.filter(
                    reg_no=info['reg_no'], 
                )

                if lines:
                    line = lines[0]

                    line.quantity = info['quantity']
                    line.save()

            except: #pylint: disable=bare-except
                # LoggerManager.log_critical_error()
                return False

        # Bulk delete
        if reg_nos_to_remove:
            TransferOrderLine.objects.filter(
                reg_no__in=reg_nos_to_remove
            ).delete()
   
        return True

    @staticmethod
    def lines_to_add(transfer_order, products_to_add):
        """
        Adds new store delivery lines

        Args:
            transfer_order (StoreDeliveryNote): Model that will parent the
            new store delivery line
            lines_to_add (list): Has dicts of product reg_nos that 
            should be added
        """

        for product_data in products_to_add:
            
            try:

                product = Product.objects.get(reg_no=product_data['product_reg_no'])

                TransferOrderLine.objects.create(
                    product=product,
                    transfer_order=transfer_order,
                    quantity=product_data['quantity']
                )

            except: #pylint: disable=bare-except
                'LoggerManager.log_critical_error()'