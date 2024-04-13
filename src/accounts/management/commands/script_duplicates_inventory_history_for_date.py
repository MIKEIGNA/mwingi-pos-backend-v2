
from decimal import Decimal
from pprint import pprint
from django.core.management.base import BaseCommand

from core.number_helpers import NumberHelpers
from inventories.models.stock_models import InventoryHistory
from sales.models import ReceiptLine
from pprint import pprint
from collections import defaultdict
from datetime import datetime
from django.utils import timezone
from decimal import Decimal

def find_duplicates(lst):
    seen = set()
    duplicates = set()
    for item in lst:
        if item in seen:
            duplicates.add(item)
        else:
            seen.add(item)
    return list(duplicates)

def analyze(duplicate_items):
    """
    Example of duplicate_items
    ['Receipt#: 100-1000**Shampoo**Computer Store**413075104913']
    """
    # print()
    duplicate_data =  []
    for item in duplicate_items:
        # print('*****************************************')
        # print(item)
        # receipt_units = 
        receipt_number = item.split("**")[0].split("#:")[1].replace(' ', '')
        product_name = item.split("**")[1]
        store_name = item.split("**")[3]
        product_reg_no = item.split("**")[2]
        receipt_reg_no = item.split("**")[4]
        count = ReceiptLine.objects.filter(
            receipt__reg_no=receipt_reg_no,
            product__reg_no=product_reg_no
        ).count()
        if not count > 1 and not count == 0:
            lines = ReceiptLine.objects.filter(
                receipt__reg_no=receipt_reg_no,
                product__reg_no=product_reg_no,
            ).values('units', 'cost_total', 'created_date')
            # print('\n Lines')
            # print(lines)
            duplicate_data.append({
                'receipt_number': receipt_number,
                'product_name': product_name,
                'store_name': store_name,
                'units': str(lines[0]['units']),
                'cost_per_product': lines[0]['cost_total']/lines[0]['units'],
                'date': str(lines[0]['created_date'].strftime("%B %d, %Y %H:%M:%S"))})
    pprint(duplicate_data)
    print(len(duplicate_data))
    # print('******************** ORDERED BY RECEIPTS **********************')
    ordered_by_receipts = defaultdict(list)
    for item in duplicate_data:ordered_by_receipts[item['receipt_number']].append(item)
    pprint(dict(ordered_by_receipts))
    # print('******************** ORDERED BY STORE NAME **********************')
    ordered_by_store_name = defaultdict(list)
    for item in duplicate_data:ordered_by_store_name[item['store_name']].append(item)
    # pprint(dict(ordered_by_store_name))
    # print(len(ordered_by_receipts))
    return ordered_by_receipts

def analyze_v2(duplicate_items):
    """
    Example of duplicate_items
    ['Receipt#: 100-1000**Shampoo**Computer Store**413075104913']
    """
    print()
    duplicate_data =  []
    for item in duplicate_items:
        print('*****************************************')
        print(item)
        receipt_number = item.split("**")[0].split("#:")[1].replace(' ', '')
        product_name = item.split("**")[1]
        store_name = item.split("**")[3]
        product_reg_no = item.split("**")[2]
        receipt_reg_no = item.split("**")[4]
        adjustment = item.split("**")[5]
        line_source_reg_no = item.split("**")[6]
        count = ReceiptLine.objects.filter(
            # receipt__reg_no=receipt_reg_no,
            # product__reg_no=product_reg_no
            reg_no=line_source_reg_no
        ).count()
        print(f'Count {count}')
        if not count > 1 and not count == 0:
            lines_count = ReceiptLine.objects.filter(
                receipt__reg_no=receipt_reg_no,
                product__reg_no=product_reg_no,
            ).count()
            history_count = InventoryHistory.objects.filter(
                change_source_reg_no=receipt_reg_no,
                product__reg_no=product_reg_no,
            ).count()
            if lines_count == history_count: continue
            print(f'Lines count {lines_count} History count {history_count}')
            lines = ReceiptLine.objects.filter(
                # receipt__reg_no=receipt_reg_no,
                # product__reg_no=product_reg_no
                reg_no=line_source_reg_no
            ).values('units', 'cost_total', 'created_date')
            print('\n Lines')
            print(lines)
            duplicate_data.append({
                'receipt_number': receipt_number,
                'product_name': product_name,
                'store_name': store_name,
                'units': str(lines[0]['units']),
                'cost_per_product': lines[0]['cost_total']/lines[0]['units'],
                'date': str(lines[0]['created_date'].strftime("%B %d, %Y %H:%M:%S"))})
    pprint(duplicate_data)
    print(len(duplicate_data))
    # print('******************** ORDERED BY RECEIPTS **********************')
    ordered_by_receipts = defaultdict(list)
    for item in duplicate_data:ordered_by_receipts[item['receipt_number']].append(item)
    pprint(dict(ordered_by_receipts))
    # print('******************** ORDERED BY STORE NAME **********************')
    ordered_by_store_name = defaultdict(list)
    for item in duplicate_data:ordered_by_store_name[item['store_name']].append(item)
    # pprint(dict(ordered_by_store_name))
    # print(len(ordered_by_receipts))
    return ordered_by_receipts

def analyze_v3(duplicate_items):
    """
    Example of duplicate_items
    ['Receipt#: 100-1000**Shampoo**Computer Store**413075104913']
    """
    # print()
    duplicate_data =  []
    for item in duplicate_items:
        # print('*****************************************')
        # print(item)
        receipt_number = item.split("**")[0].split("#:")[1].replace(' ', '')
        product_name = item.split("**")[1]
        store_name = item.split("**")[3]
        product_reg_no = item.split("**")[2]
        receipt_reg_no = item.split("**")[4]
        adjustment = item.split("**")[5]
        receipt_units = Decimal(adjustment)
        # If receipt units is negative, turn it to positive and vice versa
        if receipt_units < 0: 
            receipt_units = abs(receipt_units)
        else: 
            receipt_units = -abs(receipt_units)
        line_count = ReceiptLine.objects.filter(
            receipt__reg_no=receipt_reg_no,
            product__reg_no=product_reg_no,
            units=receipt_units
        ).count()
        history_count = InventoryHistory.objects.filter(
            change_source_reg_no=receipt_reg_no,
            product__reg_no=product_reg_no,
            adjustment=adjustment
        ).count()
        # print(f'Line count {line_count} History count {history_count}')
        if (line_count == history_count) or Decimal(adjustment) == 0: continue
        duplicate_times = (history_count - line_count) 
        # print(f'Duplicate times {duplicate_times}')
        # print(
        #     {
        #         'receipt_number': receipt_number,
        #         'product_name': product_name,
        #         'store_name': store_name,
        #         'units': adjustment,
        #     }
        # )
        if duplicate_times:
            lines = ReceiptLine.objects.filter(
                receipt__reg_no=receipt_reg_no,
                product__reg_no=product_reg_no,
                units=receipt_units
            ).values('units', 'cost_total', 'total_amount', 'tax_rate',  'created_date')
            for _ in range(duplicate_times):
                tax_rate = lines[0]['tax_rate']
                net_sales = lines[0]['total_amount']
                taxes = 0
                if tax_rate > 0:
                    taxes = NumberHelpers.normal_round(
                        (net_sales / (tax_rate + 100)) * tax_rate,
                        2
                    )
                duplicate_data.append({
                'receipt_number': receipt_number,
                'product_name': product_name,
                'store_name': store_name,
                'units': str(lines[0]['units']),
                'net_sales': str(net_sales),
                'taxes': str(taxes),
                'cost_per_product': lines[0]['cost_total']/lines[0]['units'],
                'date': str(lines[0]['created_date'].strftime("%B %d, %Y %H:%M:%S"))})
    pprint(duplicate_data)
    print(len(duplicate_data))
    # print('******************** ORDERED BY RECEIPTS **********************')
    ordered_by_receipts = defaultdict(list)
    for item in duplicate_data:ordered_by_receipts[item['receipt_number']].append(item)
    pprint(dict(ordered_by_receipts))
    # print('******************** ORDERED BY STORE NAME **********************')
    ordered_by_store_name = defaultdict(list)
    for item in duplicate_data:ordered_by_store_name[item['store_name']].append(item)
    # pprint(dict(ordered_by_store_name))
    # print(len(ordered_by_receipts))
    return ordered_by_receipts

def group_by_store_name(data):
    ordered_by_store_name = defaultdict(list)
    for item in data:
        ordered_by_store_name[item['store_name']].append(item)
    return dict(ordered_by_store_name)

def analyze_loss_data(data):
    group_by_shop_name = []
    for key, value in data.items():
        group_by_shop_name.append(group_by_store_name(data[key]))
    # print('*****************************************************')
    # pprint(group_by_shop_name)
    # Get shop names in dict
    shop_names = {}
    for item in group_by_shop_name:
        for key, value in item.items():
            shop_names[key] = {}
    # print('*****************************************************')
    # pprint(shop_names)
    for item in group_by_shop_name:
        for key, value in item.items():
            # for v in value:
            #     if v['product_name'] in shop_names[key]:
            #         shop_names[key][v['product_name']] += Decimal(v['units'])
            #     else:
            #         shop_names[key][v['product_name']] = Decimal(v['units'])
            for v in value:
                if v['product_name'] in shop_names[key]:
                    shop_names[key][v['product_name']]['units'] += Decimal(v['units'])
                    shop_names[key][v['product_name']]['net_sales'] += Decimal(v['net_sales'])
                    shop_names[key][v['product_name']]['taxes'] += Decimal(v['taxes'])
                else:
                    shop_names[key][v['product_name']] = {
                        'units': Decimal(v['units']),
                        'net_sales': Decimal(v['net_sales']),
                        'taxes': Decimal(v['taxes']),
                    }
    print('*****************************************************')
    return shop_names

def check(from_year, from_month, from_day, to_year, to_month, to_day):
    histories = InventoryHistory.objects.filter(
        store__profile__user__email="email@gmail.com",
        reason=InventoryHistory.INVENTORY_HISTORY_SALE,
        # store__reg_no__in=[396491159149,],
        created_date__gte=datetime(from_year, from_month, from_day, 0, 0, 0, 0, timezone.utc),
        created_date__lte=datetime(to_year, to_month, to_day, 23, 59, 0, 0, timezone.utc),
    ).values_list(
        'change_source_name', 
        'product__name', 
        'product__reg_no', 
        'store__name', 
        'change_source_reg_no',
    ).order_by('change_source_name', 'created_date')
    regs = []
    for his in histories: regs.append(f"{his[0]}**{his[1]}**{his[2]}**{his[3]}**{his[4]}")
    duplicate_items = find_duplicates(regs)
    # pprint(duplicate_items)
    # print(len(duplicate_items))
    data = analyze(duplicate_items)
    pprint(analyze_loss_data(data))



    # histories = InventoryHistory.objects.filter(
    #     store__profile__user__email="email@gmail.com",
    #     reason=InventoryHistory.INVENTORY_HISTORY_SALE,
    #     # store__reg_no__in=[396491159149,],
    #     created_date__gte=datetime(year, month, day, 0, 0, 0, 0, timezone.utc),
    #     # created_date__lte=datetime(year, month, day, 23, 59, 0, 0, timezone.utc),
    # ).values_list(
    #     'change_source_name', 
    #     'product__name', 
    #     'product__reg_no', 
    #     'store__name', 
    #     'change_source_reg_no',
    # ).order_by('change_source_name', 'created_date')
    # regs = []
    # for his in histories: regs.append(f"{his[0]}**{his[1]}**{his[2]}**{his[3]}**{his[4]}")
    # duplicate_items = find_duplicates(regs)
    # # pprint(duplicate_items)
    # # print(len(duplicate_items))
    # analyze(duplicate_items)

def checkdups(from_year, from_month, from_day, to_year, to_month, to_day):
    histories = InventoryHistory.objects.filter(
        store__profile__user__email="email@gmail.com",
        reason=InventoryHistory.INVENTORY_HISTORY_SALE,
        # store__reg_no__in=[423048554267,],
        # product__reg_no__in=[433654759982,],
        created_date__gte=datetime(from_year, from_month, from_day, 0, 0, 0, 0, timezone.utc),
        created_date__lte=datetime(to_year, to_month, to_day, 23, 59, 0, 0, timezone.utc),
    ).values_list(
        'change_source_name', 
        'product__name', 
        'product__reg_no', 
        'store__name', 
        'change_source_reg_no',
        'adjustment',
        'line_source_reg_no'
    ).order_by('change_source_name', 'created_date')
    regs = []
    for his in histories:
        line = f"{his[0]}**{his[1]}**{his[2]}**{his[3]}**{his[4]}**{his[5]}"
        # print(line)
        regs.append(line)
    duplicate_items = find_duplicates(regs)
    # print('\n Duplicate items')
    # pprint(duplicate_items)
    # print(len(duplicate_items))
    data = analyze(duplicate_items)
    pprint(analyze_loss_data(data))

def checkdups_v2(from_year, from_month, from_day, to_year, to_month, to_day):
    histories = InventoryHistory.objects.filter(
        store__profile__user__email="email@gmail.com",
        reason=InventoryHistory.INVENTORY_HISTORY_SALE,
        store__reg_no__in=[423048554267,],
        product__reg_no__in=[433654759982,],
        created_date__gte=datetime(from_year, from_month, from_day, 0, 0, 0, 0, timezone.utc),
        created_date__lte=datetime(to_year, to_month, to_day, 23, 59, 0, 0, timezone.utc),
    ).values_list(
        'change_source_name', 
        'product__name', 
        'product__reg_no', 
        'store__name', 
        'change_source_reg_no',
        'adjustment',
        'line_source_reg_no'
    ).order_by('change_source_name', 'created_date')
    regs = []
    for his in histories:
        line = f"{his[0]}**{his[1]}**{his[2]}**{his[3]}**{his[4]}**{his[5]}**{his[6]}"
        # print(line)
        regs.append(line)
    duplicate_items = find_duplicates(regs)
    print('\n Duplicate items')
    pprint(duplicate_items)
    # print(len(duplicate_items))
    data = analyze_v2(duplicate_items)
    pprint(analyze_loss_data(data))

def checkdups_v3(from_year, from_month, from_day, to_year, to_month, to_day):
    histories = InventoryHistory.objects.filter(
        store__profile__user__email="email@gmail.com",
        reason=InventoryHistory.INVENTORY_HISTORY_SALE,
        # store__reg_no__in=[423048554267,],
        # product__reg_no__in=[433654759982,],
        created_date__gte=datetime(from_year, from_month, from_day, 0, 0, 0, 0, timezone.utc),
        created_date__lte=datetime(to_year, to_month, to_day, 23, 59, 0, 0, timezone.utc),
    ).values_list(
        'change_source_name', 
        'product__name', 
        'product__reg_no', 
        'store__name', 
        'change_source_reg_no',
        'adjustment',
        'line_source_reg_no'
    ).order_by('change_source_name', 'created_date')
    regs = []
    for his in histories:
        line = f"{his[0]}**{his[1]}**{his[2]}**{his[3]}**{his[4]}**{his[5]}"
        # print(line)
        regs.append(line)
    duplicate_items = find_duplicates(regs)
    # print('\n Duplicate items')
    # pprint(duplicate_items)
    # print(len(duplicate_items))
    data = analyze_v3(duplicate_items)
    pprint(analyze_loss_data(data))

def check_for_soft_dups(from_year, from_month, from_day, to_year, to_month, to_day):
    histories = InventoryHistory.objects.filter(
        store__profile__user__email="email@gmail.com",
        reason=InventoryHistory.INVENTORY_HISTORY_SALE,
        # store__reg_no__in=[438394492861,],
        # product__reg_no__in=[475044577764,],
        # store__reg_no__in=[423048554267,],
        # product__reg_no__in=[433654759982,],
        created_date__gte=datetime(from_year, from_month, from_day, 0, 0, 0, 0, timezone.utc),
        created_date__lte=datetime(to_year, to_month, to_day, 23, 59, 0, 0, timezone.utc),
    ).values_list(
        'change_source_name', 
        'product__name', 
        'product__reg_no', 
        'store__name', 
        'change_source_reg_no',
    ).order_by('change_source_name', 'created_date')
    regs = []
    for his in histories: regs.append(f"{his[0]}**{his[1]}**{his[2]}**{his[3]}**{his[4]}")
    duplicate_items = find_duplicates(regs)
    pprint(duplicate_items)
    for duplicate in duplicate_items:
        change_source_name = duplicate.split("**")[0]
        product_name = duplicate.split("**")[1]
        store_name = duplicate.split("**")[3]
        print(f"\n*** Checking for {change_source_name} {product_name} {store_name}\n")
        histories = InventoryHistory.objects.filter(
            change_source_name=change_source_name,
            product__name=product_name,
            store__name=store_name
        ).order_by('created_date')
        for index, history in enumerate(histories):
            print(f"{history.product} {history.adjustment} {history.stock_after} {history.created_date}")
            history.created_date += timezone.timedelta(milliseconds=index)
            history.save()
        histories = InventoryHistory.objects.filter(
            change_source_name=change_source_name,
            product__name=product_name,
            store__name=store_name
        ).order_by('created_date')
        print('**')
        for index, history in enumerate(histories):
            print(f"{history.product} {history.adjustment} {history.stock_after} {history.created_date}")
        
       
    # print(len(duplicate_items))
    # data = analyze(duplicate_items)
    # pprint(analyze_loss_data(data))


class Command(BaseCommand):
    """ 
    To call this command,
    
    python manage.py script_duplicates_inventory_history_for_date strict 2024 01 06 2024 01 06
    python manage.py script_duplicates_inventory_history_for_date non-strict 2023 12 23 2023 12 23


    python manage.py script_duplicates_inventory_history_for_date strict 2024 1 9 2024 1 17
    python manage.py script_duplicates_inventory_history_for_date non-strict 2024 1 9 2024 1 9



    python manage.py script_duplicates_inventory_history_for_date non-strict 2024 1 4 2024 1 4
    python manage.py script_duplicates_inventory_history_for_date strict 2024 01 26 2024 02 01


    python manage.py script_duplicates_inventory_history_for_date soft-strict 2023 12 13 2023 12 13

    python manage.py script_duplicates_inventory_history_for_date strict-v3 2023 12 23 2024 1 31

    python manage.py script_duplicates_inventory_history_for_date strict-v3 2024 2 1 2024 03 30

    
    Retrieve receipts for the specified hours 
    """
    help = 'Used to retrieve receipts for the specified hours'

    def add_arguments(self, parser):
        parser.add_argument('strict', type=str)
        parser.add_argument('from_year', type=str)
        parser.add_argument('from_month', type=str)
        parser.add_argument('from_day', type=str)

        parser.add_argument('to_year', type=str)
        parser.add_argument('to_month', type=str)
        parser.add_argument('to_day', type=str)

    def handle(self, *args, **options):

        from_year = int(options['from_year'])
        from_month = int(options['from_month'])
        from_day = int(options['from_day'])

        to_year = int(options['to_year'])
        to_month = int(options['to_month'])
        to_day = int(options['to_day'])

        print(f'Checking for date {from_year}-{from_month}-{from_day} to {to_year}-{to_month}-{to_day}')

        if options['strict'] == 'non-strict':
            print("----------------################# CHECKING FOR DUPLICATES #################")
            check(from_year, from_month, from_day, to_year, to_month, to_day)

        elif options['strict'] == 'strict':

            print("----------------################# CHECKING FOR DUPLICATES WITH ADJUSTMENTS #################")
            checkdups(from_year, from_month, from_day, to_year, to_month, to_day)

        elif options['strict'] == 'soft-strict':

            print("----------------################# CHECKING FOR SOFT DUPLICATES #################")
            check_for_soft_dups(from_year, from_month, from_day, to_year, to_month, to_day)

        elif options['strict'] == 'strict-v3':
                print("----------------################# CHECKING FOR DUPLICATES WITH ADJUSTMENTS V3 #################")
                checkdups_v3(from_year, from_month, from_day, to_year, to_month, to_day)
        


'''
check(2023, 12, 23, 2023, 12, 26)
check(2023, 12, 25, 2023, 12, 25)
checkdups(2023, 12, 25, 2023, 12, 25)


check_for_soft_dups(2023, 12, 12, 2024, 1, 23)

check(2024, 1, 9, 2024, 1, 9)
pyth

checkdups_v2(2024, 1, 6, 2024, 1, 6)
checkdups(2024, 1, 1, 2024, 1, 31)
checkdups_v3(2023, 12, 23, 2024, 1, 31)
'''