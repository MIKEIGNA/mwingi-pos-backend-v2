import copy
import datetime
from decimal import Decimal
from pprint import pprint

from django.utils import timezone
from django.conf import settings
from django.test import TestCase

from core.test_utils.custom_testcase import TestCase, empty_logfiles
from accounts.models import UserGroup

from core.test_utils.create_user import create_new_user
from core.test_utils.log_reader import get_test_firebase_sender_log_content
from core.test_utils.loyverse_data.customers_data import LOYVERSE_CUSTOMER_DATA
from core.test_utils.loyverse_data.employees_data import LOYVERSE_EMPLOYEE_DATA
from core.test_utils.loyverse_data.loyverse_test_data import (
    LOYVERSE_CATEGORY_DATA,
    LOYVERSE_INVENTORY_LEVELS,
    LOYVERSE_ITEM_DATA,
    LOYVERSE_STORE_DATA,
    LOYVERSE_TAX_DATA,
)
from inventories.models import StockLevel
from loyverse.utils.loyverse_api import LoyverseSyncData
from products.models import Product, ProductBundle
from stores.models import Category, Store, Tax
from profiles.models import Customer, EmployeeProfile, Profile

class LoyverseSyncDataApiTestCase(TestCase):
    def setUp(self):
        # Create a user with email john@gmail.com
        self.user1 = create_new_user("angelina")
        self.user2 = create_new_user("john")

        self.profile1 = Profile.objects.get(
            user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT
        )
        self.profile2 = Profile.objects.get(user__email="john@gmail.com")

    def call_sync_data(
        self,
        profile,
        loyverse_stores_data=copy.deepcopy(LOYVERSE_STORE_DATA),
        loyverse_employees_data=copy.deepcopy(LOYVERSE_EMPLOYEE_DATA),
        loyverse_tax_data=copy.deepcopy(LOYVERSE_TAX_DATA),
        loyverse_category_data=copy.deepcopy(LOYVERSE_CATEGORY_DATA),
        loyverse_customer_data=copy.deepcopy(LOYVERSE_CUSTOMER_DATA),
        loyverse_items_data=copy.deepcopy(LOYVERSE_ITEM_DATA),
        loyverse_levels_data=copy.deepcopy(LOYVERSE_INVENTORY_LEVELS),
    ):
        # We use deepcopy so that we dont edit the global LOYVERSE_ITEM_DATA

        LoyverseSyncData(
            profile=profile,
            stores=loyverse_stores_data,
            employees=loyverse_employees_data,
            taxes=loyverse_tax_data,
            categories=loyverse_category_data,
            customers=loyverse_customer_data,
            items=loyverse_items_data,
            levels=loyverse_levels_data,
        ).sync_data()
    '''
    
    def test_if_stock_level_models_were_created_and_updated_correctly(self):
        """
        Since we have so many stock levels, we combine 2 tests into one.

        1. We check if stock levels are updated correctly
        2. We call sync data twice to see if nothing will get updated if 
           stock levels are upto date
        """
        # Create data
        with self.assertNumQueries(581):
            self.call_sync_data(self.profile1)

        with self.assertNumQueries(165):
            self.call_sync_data(self.profile1)

        levels = StockLevel.objects.all().order_by("id")

        self.assertEqual(levels.count(), 36)

        #### Models for product 1
        self.assertEqual(levels[0].store.name, LOYVERSE_STORE_DATA["stores"][0]["name"])
        self.assertEqual(
            levels[0].product.name, LOYVERSE_ITEM_DATA["items"][0]["item_name"]
        )
        self.assertEqual(levels[0].price, Decimal("300.00"))
        self.assertEqual(
            levels[0].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][0]["in_stock"],
        )

        self.assertEqual(levels[1].store.name, LOYVERSE_STORE_DATA["stores"][1]["name"])
        self.assertEqual(
            levels[1].product.name, LOYVERSE_ITEM_DATA["items"][0]["item_name"]
        )
        self.assertEqual(levels[1].price, Decimal("300.00"))
        self.assertEqual(
            levels[1].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][12]["in_stock"],
        )

        self.assertEqual(levels[2].store.name, LOYVERSE_STORE_DATA["stores"][2]["name"])
        self.assertEqual(
            levels[2].product.name, LOYVERSE_ITEM_DATA["items"][0]["item_name"]
        )
        self.assertEqual(levels[2].price, Decimal("300.00"))
        self.assertEqual(levels[2].units, 0)

        self.assertEqual(levels[3].store.name, LOYVERSE_STORE_DATA["stores"][3]["name"])
        self.assertEqual(
            levels[3].product.name, LOYVERSE_ITEM_DATA["items"][0]["item_name"]
        )
        self.assertEqual(levels[3].price, Decimal("300.00"))
        self.assertEqual(levels[3].units, 0)

        self.assertEqual(levels[4].store.name, LOYVERSE_STORE_DATA["stores"][4]["name"])
        self.assertEqual(
            levels[4].product.name, LOYVERSE_ITEM_DATA["items"][0]["item_name"]
        )
        self.assertEqual(levels[4].price, Decimal("300.00"))
        self.assertEqual(levels[4].units, 0)

        self.assertEqual(levels[5].store.name, LOYVERSE_STORE_DATA["stores"][5]["name"])
        self.assertEqual(
            levels[5].product.name, LOYVERSE_ITEM_DATA["items"][0]["item_name"]
        )
        self.assertEqual(levels[5].price, Decimal("300.00"))
        self.assertEqual(levels[5].units, 0)

        #### Models for product 2
        self.assertEqual(levels[6].store.name, LOYVERSE_STORE_DATA["stores"][0]["name"])
        self.assertEqual(
            levels[6].product.name, LOYVERSE_ITEM_DATA["items"][1]["item_name"]
        )
        self.assertEqual(levels[6].price, Decimal("200.00"))
        self.assertEqual(
            levels[6].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][1]["in_stock"],
        )

        self.assertEqual(levels[7].store.name, LOYVERSE_STORE_DATA["stores"][1]["name"])
        self.assertEqual(
            levels[7].product.name, LOYVERSE_ITEM_DATA["items"][1]["item_name"]
        )
        self.assertEqual(levels[7].price, Decimal("200.00"))
        self.assertEqual(
            levels[7].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][13]["in_stock"],
        )

        self.assertEqual(levels[8].store.name, LOYVERSE_STORE_DATA["stores"][2]["name"])
        self.assertEqual(
            levels[8].product.name, LOYVERSE_ITEM_DATA["items"][1]["item_name"]
        )
        self.assertEqual(levels[8].price, Decimal("200.00"))
        self.assertEqual(levels[8].units, 0)

        self.assertEqual(levels[9].store.name, LOYVERSE_STORE_DATA["stores"][3]["name"])
        self.assertEqual(
            levels[9].product.name, LOYVERSE_ITEM_DATA["items"][1]["item_name"]
        )
        self.assertEqual(levels[9].price, Decimal("200.00"))
        self.assertEqual(levels[9].units, 0)

        self.assertEqual(
            levels[10].store.name, LOYVERSE_STORE_DATA["stores"][4]["name"]
        )
        self.assertEqual(
            levels[10].product.name, LOYVERSE_ITEM_DATA["items"][1]["item_name"]
        )
        self.assertEqual(levels[10].price, Decimal("200.00"))
        self.assertEqual(levels[10].units, 0)

        self.assertEqual(
            levels[11].store.name, LOYVERSE_STORE_DATA["stores"][5]["name"]
        )
        self.assertEqual(
            levels[11].product.name, LOYVERSE_ITEM_DATA["items"][1]["item_name"]
        )
        self.assertEqual(levels[11].price, Decimal("200.00"))
        self.assertEqual(levels[11].units, 0)

        #### Models for product 3
        self.assertEqual(
            levels[12].store.name, LOYVERSE_STORE_DATA["stores"][0]["name"]
        )
        self.assertEqual(
            levels[12].product.name, LOYVERSE_ITEM_DATA["items"][2]["item_name"]
        )
        self.assertEqual(levels[12].price, Decimal("450.00"))
        self.assertEqual(
            levels[12].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][2]["in_stock"],
        )

        self.assertEqual(
            levels[13].store.name, LOYVERSE_STORE_DATA["stores"][1]["name"]
        )
        self.assertEqual(
            levels[13].product.name, LOYVERSE_ITEM_DATA["items"][2]["item_name"]
        )
        self.assertEqual(levels[13].price, Decimal("450.00"))
        self.assertEqual(
            levels[13].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][14]["in_stock"],
        )

        self.assertEqual(
            levels[14].store.name, LOYVERSE_STORE_DATA["stores"][2]["name"]
        )
        self.assertEqual(
            levels[14].product.name, LOYVERSE_ITEM_DATA["items"][2]["item_name"]
        )
        self.assertEqual(levels[14].price, Decimal("450.00"))
        self.assertEqual(levels[14].units, 0)

        self.assertEqual(
            levels[15].store.name, LOYVERSE_STORE_DATA["stores"][3]["name"]
        )
        self.assertEqual(
            levels[15].product.name, LOYVERSE_ITEM_DATA["items"][2]["item_name"]
        )
        self.assertEqual(levels[15].price, Decimal("450.00"))
        self.assertEqual(levels[15].units, 0)

        self.assertEqual(
            levels[16].store.name, LOYVERSE_STORE_DATA["stores"][4]["name"]
        )
        self.assertEqual(
            levels[16].product.name, LOYVERSE_ITEM_DATA["items"][2]["item_name"]
        )
        self.assertEqual(levels[16].price, Decimal("450.00"))
        self.assertEqual(levels[16].units, 0)

        self.assertEqual(
            levels[17].store.name, LOYVERSE_STORE_DATA["stores"][5]["name"]
        )
        self.assertEqual(
            levels[17].product.name, LOYVERSE_ITEM_DATA["items"][2]["item_name"]
        )
        self.assertEqual(levels[17].price, Decimal("450.00"))
        self.assertEqual(levels[17].units, 0)

        #### Models for product 4
        self.assertEqual(
            levels[18].store.name, LOYVERSE_STORE_DATA["stores"][0]["name"]
        )
        self.assertEqual(
            levels[18].product.name, LOYVERSE_ITEM_DATA["items"][4]["item_name"]
        )
        self.assertEqual(levels[18].price, Decimal("500.00"))
        self.assertEqual(
            levels[18].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][10]["in_stock"],
        )

        self.assertEqual(
            levels[19].store.name, LOYVERSE_STORE_DATA["stores"][1]["name"]
        )
        self.assertEqual(
            levels[19].product.name, LOYVERSE_ITEM_DATA["items"][4]["item_name"]
        )
        self.assertEqual(levels[19].price, Decimal("500.00"))
        self.assertEqual(
            levels[19].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][22]["in_stock"],
        )

        self.assertEqual(
            levels[20].store.name, LOYVERSE_STORE_DATA["stores"][2]["name"]
        )
        self.assertEqual(
            levels[20].product.name, LOYVERSE_ITEM_DATA["items"][4]["item_name"]
        )
        self.assertEqual(levels[20].price, Decimal("500.00"))
        self.assertEqual(levels[20].units, 0)

        self.assertEqual(
            levels[21].store.name, LOYVERSE_STORE_DATA["stores"][3]["name"]
        )
        self.assertEqual(
            levels[21].product.name, LOYVERSE_ITEM_DATA["items"][4]["item_name"]
        )
        self.assertEqual(levels[21].price, Decimal("500.00"))
        self.assertEqual(levels[21].units, 0)

        self.assertEqual(
            levels[22].store.name, LOYVERSE_STORE_DATA["stores"][4]["name"]
        )
        self.assertEqual(
            levels[22].product.name, LOYVERSE_ITEM_DATA["items"][4]["item_name"]
        )
        self.assertEqual(levels[22].price, Decimal("500.00"))
        self.assertEqual(levels[22].units, 0)

        self.assertEqual(
            levels[23].store.name, LOYVERSE_STORE_DATA["stores"][5]["name"]
        )
        self.assertEqual(
            levels[23].product.name, LOYVERSE_ITEM_DATA["items"][4]["item_name"]
        )
        self.assertEqual(levels[23].price, Decimal("500.00"))
        self.assertEqual(levels[23].units, 0)

        #### Models for product 5
        self.assertEqual(
            levels[24].store.name, LOYVERSE_STORE_DATA["stores"][0]["name"]
        )
        self.assertEqual(
            levels[24].product.name, LOYVERSE_ITEM_DATA["items"][5]["item_name"]
        )
        self.assertEqual(levels[24].price, Decimal("750.00"))
        self.assertEqual(
            levels[24].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][11]["in_stock"],
        )

        self.assertEqual(
            levels[25].store.name, LOYVERSE_STORE_DATA["stores"][1]["name"]
        )
        self.assertEqual(
            levels[25].product.name, LOYVERSE_ITEM_DATA["items"][5]["item_name"]
        )
        self.assertEqual(levels[25].price, Decimal("750.00"))
        self.assertEqual(
            levels[25].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][23]["in_stock"],
        )

        self.assertEqual(
            levels[26].store.name, LOYVERSE_STORE_DATA["stores"][2]["name"]
        )
        self.assertEqual(
            levels[26].product.name, LOYVERSE_ITEM_DATA["items"][5]["item_name"]
        )
        self.assertEqual(levels[26].price, Decimal("750.00"))
        self.assertEqual(levels[26].units, 0)

        self.assertEqual(
            levels[27].store.name, LOYVERSE_STORE_DATA["stores"][3]["name"]
        )
        self.assertEqual(
            levels[27].product.name, LOYVERSE_ITEM_DATA["items"][5]["item_name"]
        )
        self.assertEqual(levels[27].price, Decimal("750.00"))
        self.assertEqual(levels[27].units, 0)

        self.assertEqual(
            levels[28].store.name, LOYVERSE_STORE_DATA["stores"][4]["name"]
        )
        self.assertEqual(
            levels[28].product.name, LOYVERSE_ITEM_DATA["items"][5]["item_name"]
        )
        self.assertEqual(levels[28].price, Decimal("750.00"))
        self.assertEqual(levels[28].units, 0)

        self.assertEqual(
            levels[29].store.name, LOYVERSE_STORE_DATA["stores"][5]["name"]
        )
        self.assertEqual(
            levels[29].product.name, LOYVERSE_ITEM_DATA["items"][5]["item_name"]
        )
        self.assertEqual(levels[29].price, Decimal("750.00"))
        self.assertEqual(levels[29].units, 0)

        ### Models for product 6
        self.assertEqual(
            levels[30].store.name, LOYVERSE_STORE_DATA["stores"][0]["name"]
        )
        self.assertEqual(
            levels[30].product.name, LOYVERSE_ITEM_DATA["items"][3]["item_name"]
        )
        self.assertEqual(levels[30].price, Decimal("3000.00"))
        self.assertEqual(
            levels[30].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][3]["in_stock"],
        )

        self.assertEqual(
            levels[31].store.name, LOYVERSE_STORE_DATA["stores"][1]["name"]
        )
        self.assertEqual(
            levels[31].product.name, LOYVERSE_ITEM_DATA["items"][3]["item_name"]
        )
        self.assertEqual(levels[31].price, Decimal("3000.00"))
        self.assertEqual(
            levels[31].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][15]["in_stock"],
        )

        self.assertEqual(
            levels[32].store.name, LOYVERSE_STORE_DATA["stores"][2]["name"]
        )
        self.assertEqual(
            levels[32].product.name, LOYVERSE_ITEM_DATA["items"][3]["item_name"]
        )
        self.assertEqual(levels[32].price, Decimal("3000.00"))
        self.assertEqual(levels[32].units, 0)

        self.assertEqual(
            levels[33].store.name, LOYVERSE_STORE_DATA["stores"][3]["name"]
        )
        self.assertEqual(
            levels[33].product.name, LOYVERSE_ITEM_DATA["items"][3]["item_name"]
        )
        self.assertEqual(levels[33].price, Decimal("3000.00"))
        self.assertEqual(levels[33].units, 0)

        self.assertEqual(
            levels[34].store.name, LOYVERSE_STORE_DATA["stores"][4]["name"]
        )
        self.assertEqual(
            levels[34].product.name, LOYVERSE_ITEM_DATA["items"][3]["item_name"]
        )
        self.assertEqual(levels[34].price, Decimal("3000.00"))
        self.assertEqual(levels[34].units, 0)

        self.assertEqual(
            levels[35].store.name, LOYVERSE_STORE_DATA["stores"][5]["name"]
        )
        self.assertEqual(
            levels[35].product.name, LOYVERSE_ITEM_DATA["items"][3]["item_name"]
        )
        self.assertEqual(levels[35].price, Decimal("3000.00"))
        self.assertEqual(levels[35].units, 0)

    def test_if_only_stock_level_models_with_differing_in_stock_values_are_updated(self):
        
        # Update data for the first time
        with self.assertNumQueries(581):
            self.call_sync_data(self.profile1)

        # Make the second stock level to have a differing in stock value
        levels = StockLevel.objects.all().order_by('id')
        level2 = levels[1]

        level2.units = 111
        level2.save()

        # Update data for the second time
        with self.assertNumQueries(172):
            self.call_sync_data(self.profile1)

        levels = StockLevel.objects.all().order_by("id")

        self.assertEqual(levels.count(), 36)

        #### Models for product 1
        self.assertEqual(levels[0].store.name, LOYVERSE_STORE_DATA["stores"][0]["name"])
        self.assertEqual(
            levels[0].product.name, LOYVERSE_ITEM_DATA["items"][0]["item_name"]
        )
        self.assertEqual(levels[0].price, Decimal("300.00"))
        self.assertEqual(
            levels[0].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][0]["in_stock"],
        )

        self.assertEqual(levels[1].store.name, LOYVERSE_STORE_DATA["stores"][1]["name"])
        self.assertEqual(
            levels[1].product.name, LOYVERSE_ITEM_DATA["items"][0]["item_name"]
        )
        self.assertEqual(levels[1].price, Decimal("300.00"))
        self.assertEqual(
            levels[1].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][12]["in_stock"],
        )

        self.assertEqual(levels[2].store.name, LOYVERSE_STORE_DATA["stores"][2]["name"])
        self.assertEqual(
            levels[2].product.name, LOYVERSE_ITEM_DATA["items"][0]["item_name"]
        )
        self.assertEqual(levels[2].price, Decimal("300.00"))
        self.assertEqual(levels[2].units, 0)

        self.assertEqual(levels[3].store.name, LOYVERSE_STORE_DATA["stores"][3]["name"])
        self.assertEqual(
            levels[3].product.name, LOYVERSE_ITEM_DATA["items"][0]["item_name"]
        )
        self.assertEqual(levels[3].price, Decimal("300.00"))
        self.assertEqual(levels[3].units, 0)

        self.assertEqual(levels[4].store.name, LOYVERSE_STORE_DATA["stores"][4]["name"])
        self.assertEqual(
            levels[4].product.name, LOYVERSE_ITEM_DATA["items"][0]["item_name"]
        )
        self.assertEqual(levels[4].price, Decimal("300.00"))
        self.assertEqual(levels[4].units, 0)

        self.assertEqual(levels[5].store.name, LOYVERSE_STORE_DATA["stores"][5]["name"])
        self.assertEqual(
            levels[5].product.name, LOYVERSE_ITEM_DATA["items"][0]["item_name"]
        )
        self.assertEqual(levels[5].price, Decimal("300.00"))
        self.assertEqual(levels[5].units, 0)

        #### Models for product 2
        self.assertEqual(levels[6].store.name, LOYVERSE_STORE_DATA["stores"][0]["name"])
        self.assertEqual(
            levels[6].product.name, LOYVERSE_ITEM_DATA["items"][1]["item_name"]
        )
        self.assertEqual(levels[6].price, Decimal("200.00"))
        self.assertEqual(
            levels[6].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][1]["in_stock"],
        )

        self.assertEqual(levels[7].store.name, LOYVERSE_STORE_DATA["stores"][1]["name"])
        self.assertEqual(
            levels[7].product.name, LOYVERSE_ITEM_DATA["items"][1]["item_name"]
        )
        self.assertEqual(levels[7].price, Decimal("200.00"))
        self.assertEqual(
            levels[7].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][13]["in_stock"],
        )

        self.assertEqual(levels[8].store.name, LOYVERSE_STORE_DATA["stores"][2]["name"])
        self.assertEqual(
            levels[8].product.name, LOYVERSE_ITEM_DATA["items"][1]["item_name"]
        )
        self.assertEqual(levels[8].price, Decimal("200.00"))
        self.assertEqual(levels[8].units, 0)

        self.assertEqual(levels[9].store.name, LOYVERSE_STORE_DATA["stores"][3]["name"])
        self.assertEqual(
            levels[9].product.name, LOYVERSE_ITEM_DATA["items"][1]["item_name"]
        )
        self.assertEqual(levels[9].price, Decimal("200.00"))
        self.assertEqual(levels[9].units, 0)

        self.assertEqual(
            levels[10].store.name, LOYVERSE_STORE_DATA["stores"][4]["name"]
        )
        self.assertEqual(
            levels[10].product.name, LOYVERSE_ITEM_DATA["items"][1]["item_name"]
        )
        self.assertEqual(levels[10].price, Decimal("200.00"))
        self.assertEqual(levels[10].units, 0)

        self.assertEqual(
            levels[11].store.name, LOYVERSE_STORE_DATA["stores"][5]["name"]
        )
        self.assertEqual(
            levels[11].product.name, LOYVERSE_ITEM_DATA["items"][1]["item_name"]
        )
        self.assertEqual(levels[11].price, Decimal("200.00"))
        self.assertEqual(levels[11].units, 0)

        #### Models for product 3
        self.assertEqual(
            levels[12].store.name, LOYVERSE_STORE_DATA["stores"][0]["name"]
        )
        self.assertEqual(
            levels[12].product.name, LOYVERSE_ITEM_DATA["items"][2]["item_name"]
        )
        self.assertEqual(levels[12].price, Decimal("450.00"))
        self.assertEqual(
            levels[12].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][2]["in_stock"],
        )

        self.assertEqual(
            levels[13].store.name, LOYVERSE_STORE_DATA["stores"][1]["name"]
        )
        self.assertEqual(
            levels[13].product.name, LOYVERSE_ITEM_DATA["items"][2]["item_name"]
        )
        self.assertEqual(levels[13].price, Decimal("450.00"))
        self.assertEqual(
            levels[13].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][14]["in_stock"],
        )

        self.assertEqual(
            levels[14].store.name, LOYVERSE_STORE_DATA["stores"][2]["name"]
        )
        self.assertEqual(
            levels[14].product.name, LOYVERSE_ITEM_DATA["items"][2]["item_name"]
        )
        self.assertEqual(levels[14].price, Decimal("450.00"))
        self.assertEqual(levels[14].units, 0)

        self.assertEqual(
            levels[15].store.name, LOYVERSE_STORE_DATA["stores"][3]["name"]
        )
        self.assertEqual(
            levels[15].product.name, LOYVERSE_ITEM_DATA["items"][2]["item_name"]
        )
        self.assertEqual(levels[15].price, Decimal("450.00"))
        self.assertEqual(levels[15].units, 0)

        self.assertEqual(
            levels[16].store.name, LOYVERSE_STORE_DATA["stores"][4]["name"]
        )
        self.assertEqual(
            levels[16].product.name, LOYVERSE_ITEM_DATA["items"][2]["item_name"]
        )
        self.assertEqual(levels[16].price, Decimal("450.00"))
        self.assertEqual(levels[16].units, 0)

        self.assertEqual(
            levels[17].store.name, LOYVERSE_STORE_DATA["stores"][5]["name"]
        )
        self.assertEqual(
            levels[17].product.name, LOYVERSE_ITEM_DATA["items"][2]["item_name"]
        )
        self.assertEqual(levels[17].price, Decimal("450.00"))
        self.assertEqual(levels[17].units, 0)

        #### Models for product 4
        self.assertEqual(
            levels[18].store.name, LOYVERSE_STORE_DATA["stores"][0]["name"]
        )
        self.assertEqual(
            levels[18].product.name, LOYVERSE_ITEM_DATA["items"][4]["item_name"]
        )
        self.assertEqual(levels[18].price, Decimal("500.00"))
        self.assertEqual(
            levels[18].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][10]["in_stock"],
        )

        self.assertEqual(
            levels[19].store.name, LOYVERSE_STORE_DATA["stores"][1]["name"]
        )
        self.assertEqual(
            levels[19].product.name, LOYVERSE_ITEM_DATA["items"][4]["item_name"]
        )
        self.assertEqual(levels[19].price, Decimal("500.00"))
        self.assertEqual(
            levels[19].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][22]["in_stock"],
        )

        self.assertEqual(
            levels[20].store.name, LOYVERSE_STORE_DATA["stores"][2]["name"]
        )
        self.assertEqual(
            levels[20].product.name, LOYVERSE_ITEM_DATA["items"][4]["item_name"]
        )
        self.assertEqual(levels[20].price, Decimal("500.00"))
        self.assertEqual(levels[20].units, 0)

        self.assertEqual(
            levels[21].store.name, LOYVERSE_STORE_DATA["stores"][3]["name"]
        )
        self.assertEqual(
            levels[21].product.name, LOYVERSE_ITEM_DATA["items"][4]["item_name"]
        )
        self.assertEqual(levels[21].price, Decimal("500.00"))
        self.assertEqual(levels[21].units, 0)

        self.assertEqual(
            levels[22].store.name, LOYVERSE_STORE_DATA["stores"][4]["name"]
        )
        self.assertEqual(
            levels[22].product.name, LOYVERSE_ITEM_DATA["items"][4]["item_name"]
        )
        self.assertEqual(levels[22].price, Decimal("500.00"))
        self.assertEqual(levels[22].units, 0)

        self.assertEqual(
            levels[23].store.name, LOYVERSE_STORE_DATA["stores"][5]["name"]
        )
        self.assertEqual(
            levels[23].product.name, LOYVERSE_ITEM_DATA["items"][4]["item_name"]
        )
        self.assertEqual(levels[23].price, Decimal("500.00"))
        self.assertEqual(levels[23].units, 0)

        #### Models for product 5
        self.assertEqual(
            levels[24].store.name, LOYVERSE_STORE_DATA["stores"][0]["name"]
        )
        self.assertEqual(
            levels[24].product.name, LOYVERSE_ITEM_DATA["items"][5]["item_name"]
        )
        self.assertEqual(levels[24].price, Decimal("750.00"))
        self.assertEqual(
            levels[24].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][11]["in_stock"],
        )

        self.assertEqual(
            levels[25].store.name, LOYVERSE_STORE_DATA["stores"][1]["name"]
        )
        self.assertEqual(
            levels[25].product.name, LOYVERSE_ITEM_DATA["items"][5]["item_name"]
        )
        self.assertEqual(levels[25].price, Decimal("750.00"))
        self.assertEqual(
            levels[25].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][23]["in_stock"],
        )

        self.assertEqual(
            levels[26].store.name, LOYVERSE_STORE_DATA["stores"][2]["name"]
        )
        self.assertEqual(
            levels[26].product.name, LOYVERSE_ITEM_DATA["items"][5]["item_name"]
        )
        self.assertEqual(levels[26].price, Decimal("750.00"))
        self.assertEqual(levels[26].units, 0)

        self.assertEqual(
            levels[27].store.name, LOYVERSE_STORE_DATA["stores"][3]["name"]
        )
        self.assertEqual(
            levels[27].product.name, LOYVERSE_ITEM_DATA["items"][5]["item_name"]
        )
        self.assertEqual(levels[27].price, Decimal("750.00"))
        self.assertEqual(levels[27].units, 0)

        self.assertEqual(
            levels[28].store.name, LOYVERSE_STORE_DATA["stores"][4]["name"]
        )
        self.assertEqual(
            levels[28].product.name, LOYVERSE_ITEM_DATA["items"][5]["item_name"]
        )
        self.assertEqual(levels[28].price, Decimal("750.00"))
        self.assertEqual(levels[28].units, 0)

        self.assertEqual(
            levels[29].store.name, LOYVERSE_STORE_DATA["stores"][5]["name"]
        )
        self.assertEqual(
            levels[29].product.name, LOYVERSE_ITEM_DATA["items"][5]["item_name"]
        )
        self.assertEqual(levels[29].price, Decimal("750.00"))
        self.assertEqual(levels[29].units, 0)

        ### Models for product 6
        self.assertEqual(
            levels[30].store.name, LOYVERSE_STORE_DATA["stores"][0]["name"]
        )
        self.assertEqual(
            levels[30].product.name, LOYVERSE_ITEM_DATA["items"][3]["item_name"]
        )
        self.assertEqual(levels[30].price, Decimal("3000.00"))
        self.assertEqual(
            levels[30].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][3]["in_stock"],
        )

        self.assertEqual(
            levels[31].store.name, LOYVERSE_STORE_DATA["stores"][1]["name"]
        )
        self.assertEqual(
            levels[31].product.name, LOYVERSE_ITEM_DATA["items"][3]["item_name"]
        )
        self.assertEqual(levels[31].price, Decimal("3000.00"))
        self.assertEqual(
            levels[31].units,
            LOYVERSE_INVENTORY_LEVELS["inventory_levels"][15]["in_stock"],
        )

        self.assertEqual(
            levels[32].store.name, LOYVERSE_STORE_DATA["stores"][2]["name"]
        )
        self.assertEqual(
            levels[32].product.name, LOYVERSE_ITEM_DATA["items"][3]["item_name"]
        )
        self.assertEqual(levels[32].price, Decimal("3000.00"))
        self.assertEqual(levels[32].units, 0)

        self.assertEqual(
            levels[33].store.name, LOYVERSE_STORE_DATA["stores"][3]["name"]
        )
        self.assertEqual(
            levels[33].product.name, LOYVERSE_ITEM_DATA["items"][3]["item_name"]
        )
        self.assertEqual(levels[33].price, Decimal("3000.00"))
        self.assertEqual(levels[33].units, 0)

        self.assertEqual(
            levels[34].store.name, LOYVERSE_STORE_DATA["stores"][4]["name"]
        )
        self.assertEqual(
            levels[34].product.name, LOYVERSE_ITEM_DATA["items"][3]["item_name"]
        )
        self.assertEqual(levels[34].price, Decimal("3000.00"))
        self.assertEqual(levels[34].units, 0)

        self.assertEqual(
            levels[35].store.name, LOYVERSE_STORE_DATA["stores"][5]["name"]
        )
        self.assertEqual(
            levels[35].product.name, LOYVERSE_ITEM_DATA["items"][3]["item_name"]
        )
        self.assertEqual(levels[35].price, Decimal("3000.00"))
        self.assertEqual(levels[35].units, 0)

    def test_if_employee_models_were_created_correctly(self):
        
        # Create data
        self.call_sync_data(self.profile1)

        employees = EmployeeProfile.objects.all().order_by("id")
        self.assertEqual(employees.count(), 4)

        emails = [
            'rebecca_nemparnat@mwingi.africa',
            'margaret_rakonik@mwingi.africa',
            'karen_nkoitiko@mwingi.africa',
            'faith_yinta_kalama@mwingi.africa'
        ]

        empooyee_ids = [
            '10367b2e-ed39-4719-b308-cafd0c271bd1',
            'b0b8e8e2-6607-4115-831e-13b4fca6613f',
            'f39ae765-ccb7-4d14-9b43-525d1b135670',
            'd0e7852d-485f-417a-97b8-f36c7fa89047'
        ]

        store_ids = [
            'eca0890b-cbd9-4172-9b34-703ef2f84705',
            '82158310-3276-4962-8210-2ca88d7e7f13',
            'eecaecb8-ca4c-48cd-a496-ea1fdd05213c',
            '5364425f-0100-438a-aeb2-ee3a28070ad2'
        ]

        for index, employee in enumerate(employees):
            # Employee 1
            cashier_group = UserGroup.objects.get(
                master_user=self.user1, ident_name='Cashier'
            )
                    
            self.assertEqual(employee.profile, self.profile1)
            self.assertEqual(
                employee.image.url, 
                f'/media/images/profiles/{employee.reg_no}_.jpg'
            )
            self.assertEqual(employee.phone, 0)
            self.assertEqual(employee.user.email, emails[index])
            self.assertEqual(str(employee.user.loyverse_employee_id), empooyee_ids[index])
            self.assertEqual(employee.reg_no, employee.user.reg_no) 
            self.assertEqual(employee.location,'')
            self.assertEqual(employee.role_name, cashier_group.ident_name)
            self.assertEqual(employee.role_reg_no, cashier_group.reg_no)
            self.assertEqual(str(employee.loyverse_employee_id), empooyee_ids[index])
            self.assertEqual(str(employee.loyverse_store_id), store_ids[index])
            self.assertEqual(employee.stores.all().count(), 1)

    def test_if_employee_models_can_be_created_multiple_stores(self):

        emails = [
            'rebecca_nemparnat@mwingi.africa',
            'margaret_rakonik@mwingi.africa',
            'karen_nkoitiko@mwingi.africa',
            'faith_yinta_kalama@mwingi.africa'
        ]

        empooyee_ids = [
            '10367b2e-ed39-4719-b308-cafd0c271bd1',
            'b0b8e8e2-6607-4115-831e-13b4fca6613f',
            'f39ae765-ccb7-4d14-9b43-525d1b135670',
            'd0e7852d-485f-417a-97b8-f36c7fa89047'
        ]

        store_ids = [
            'eca0890b-cbd9-4172-9b34-703ef2f84705',
            '82158310-3276-4962-8210-2ca88d7e7f13',
            'eecaecb8-ca4c-48cd-a496-ea1fdd05213c',
            '5364425f-0100-438a-aeb2-ee3a28070ad2'
        ]

        employees_data = copy.deepcopy(LOYVERSE_EMPLOYEE_DATA)
        employees_data['employees'][0]['stores'] = store_ids 

        for employee in employees_data['employees']:
            employee['stores'] = [  
                store_ids[0],
                store_ids[1],
                store_ids[2],
                store_ids[3]
            ]  
                    
        # Create data
        self.call_sync_data(self.profile1, loyverse_employees_data=employees_data)

        employees = EmployeeProfile.objects.all().order_by("id")
        self.assertEqual(employees.count(), 4)

        for index, employee in enumerate(employees):
            # Employee 1
            cashier_group = UserGroup.objects.get(
                master_user=self.user1, ident_name='Cashier'
            )
                    
            self.assertEqual(employee.profile, self.profile1)
            self.assertEqual(
                employee.image.url, 
                f'/media/images/profiles/{employee.reg_no}_.jpg'
            )
            self.assertEqual(employee.phone, 0)
            self.assertEqual(employee.user.email, emails[index])
            self.assertEqual(str(employee.user.loyverse_employee_id), empooyee_ids[index])
            self.assertEqual(employee.reg_no, employee.user.reg_no) 
            self.assertEqual(employee.location,'')
            self.assertEqual(employee.role_name, cashier_group.ident_name)
            self.assertEqual(employee.role_reg_no, cashier_group.reg_no)
            self.assertEqual(str(employee.loyverse_employee_id), empooyee_ids[index])
            self.assertEqual(employee.stores.all().count(), 4)

    def test_if_employee_models_can_be_uptated_multiple_stores(self):

        emails = [
            'rebecca_nemparnat@mwingi.africa',
            'margaret_rakonik@mwingi.africa',
            'karen_nkoitiko@mwingi.africa',
            'faith_yinta_kalama@mwingi.africa'
        ]

        empooyee_ids = [
            '10367b2e-ed39-4719-b308-cafd0c271bd1',
            'b0b8e8e2-6607-4115-831e-13b4fca6613f',
            'f39ae765-ccb7-4d14-9b43-525d1b135670',
            'd0e7852d-485f-417a-97b8-f36c7fa89047'
        ]

        store_ids = [
            'eca0890b-cbd9-4172-9b34-703ef2f84705',
            '82158310-3276-4962-8210-2ca88d7e7f13',
            'eecaecb8-ca4c-48cd-a496-ea1fdd05213c',
            '5364425f-0100-438a-aeb2-ee3a28070ad2'
        ]

        employees_data = copy.deepcopy(LOYVERSE_EMPLOYEE_DATA)
        employees_data['employees'][0]['stores'] = store_ids 

        for employee in employees_data['employees']:
            employee['stores'] = [  
                store_ids[0],
                store_ids[1],
                store_ids[2],
                store_ids[3]
            ]  
                    
        # Create data
        self.call_sync_data(self.profile1, loyverse_employees_data=employees_data)

        employees = EmployeeProfile.objects.all().order_by("id")
        self.assertEqual(employees.count(), 4)
        

        # Clear the stores
        for employee in employees:
            employee.stores.clear()
            self.assertEqual(employee.stores.all().count(), 0)

        # Update data
        self.call_sync_data(self.profile1, loyverse_employees_data=employees_data)

        employees = EmployeeProfile.objects.all().order_by("id")
        for employee in employees:
            self.assertEqual(employee.stores.all().count(), 4)

    def test_if_employees_cannot_be_duplicated_when_sync_data_has_been_called_twice(self):

        # Try to create data twice
        self.call_sync_data(self.profile1)
        self.call_sync_data(self.profile1)

        employees = EmployeeProfile.objects.all().order_by('id')

        self.assertEqual(employees.count(), len(LOYVERSE_EMPLOYEE_DATA['employees']))
    
    def test_if_2_users_can_have_the_same_products(self):

        #### Create data for user 1
        self.call_sync_data(profile=self.profile1)

        products = Product.objects.filter(profile=self.profile1).order_by('id')
        self.assertEqual(products.count(), 6)

        customers = Customer.objects.filter(profile=self.profile1).order_by('id')
        self.assertEqual(customers.count(), 3)

        taxes = Tax.objects.filter(profile=self.profile1).order_by('id')
        self.assertEqual(taxes.count(), 4)

        categories = Category.objects.filter(profile=self.profile1).order_by('id')
        self.assertEqual(categories.count(), 12)

        stores = Store.objects.filter(profile=self.profile1).order_by('id')
        self.assertEqual(stores.count(), 6)
        

        #### Create data for user 2
        self.call_sync_data(profile=self.profile2)

        products = Product.objects.filter(profile=self.profile2).order_by('id')
        self.assertEqual(products.count(), 6)

        customers = Customer.objects.filter(profile=self.profile2).order_by('id')
        self.assertEqual(customers.count(), 3)

        taxes = Tax.objects.filter(profile=self.profile2).order_by('id')
        self.assertEqual(taxes.count(), 4)

        categories = Category.objects.filter(profile=self.profile2).order_by('id')
        self.assertEqual(categories.count(), 12)

        stores = Store.objects.filter(profile=self.profile2).order_by('id')
        self.assertEqual(stores.count(), 6)


    def test_if_product_models_were_created_correctly(self):

        # Create data
        self.call_sync_data(profile=self.profile1)

        products = Product.objects.all().order_by('id')
        
        self.assertEqual(products.count(), 6)

        today = (timezone.now()).strftime("%B, %d, %Y")

        tax1 = Tax.objects.get(profile=self.profile1, name='VAT - 14.0')

        category1 = Category.objects.get(profile=self.profile1, name='Wholesale')

        # Product 1
        product1 = products[0]

        self.assertEqual(product1.profile, self.profile1)
        self.assertEqual(product1.stores.all().count(), 6)
        self.assertEqual(product1.tax, tax1)
        self.assertEqual(product1.category, category1)
        self.assertEqual(product1.bundles.all().count(), 0)
        self.assertEqual(product1.modifiers.all().count(), 0)
        self.assertEqual(product1.image.url, f'/media/images/products/{product1.reg_no}_.jpg')
        self.assertEqual(product1.color_code, settings.DEFAULT_COLOR_CODE)
        self.assertEqual(product1.name, LOYVERSE_ITEM_DATA['items'][0]['item_name'])
        self.assertEqual(product1.cost, LOYVERSE_ITEM_DATA['items'][0]['variants'][0]['cost'])
        self.assertEqual(product1.price, Decimal('300'))
        self.assertEqual(product1.sku, LOYVERSE_ITEM_DATA['items'][0]['variants'][0]['sku'])
        self.assertEqual(product1.barcode, LOYVERSE_ITEM_DATA['items'][0]['variants'][0]['barcode'])
        self.assertEqual(product1.sold_by_each, True)
        self.assertEqual(product1.is_bundle, False)
        self.assertEqual(product1.track_stock, True)
        self.assertEqual(product1.variant_count, 0)
        self.assertEqual(product1.is_variant_child, False)
        self.assertEqual(product1.show_product, True)
        self.assertEqual(product1.show_image, False)
        self.assertTrue(product1.reg_no > 100000)  # Check if we have a valid reg_no
        self.assertEqual((product1.created_date).strftime("%B, %d, %Y"), today)

        # Product 2
        product2 = products[1]

        self.assertEqual(product2.profile, self.profile1)
        self.assertEqual(product2.stores.all().count(), 6)
        self.assertEqual(product2.tax, None)
        self.assertEqual(product2.category, category1)
        self.assertEqual(product2.bundles.all().count(), 0)
        self.assertEqual(product2.modifiers.all().count(), 0)
        self.assertEqual(product2.image.url, f'/media/images/products/{product2.reg_no}_.jpg')
        self.assertEqual(product2.color_code, settings.DEFAULT_COLOR_CODE)
        self.assertEqual(product2.name, LOYVERSE_ITEM_DATA['items'][1]['item_name'])
        self.assertEqual(product2.cost, LOYVERSE_ITEM_DATA['items'][1]['variants'][0]['cost'])
        self.assertEqual(product2.price, Decimal('200.00'))
        self.assertEqual(product2.sku, LOYVERSE_ITEM_DATA['items'][1]['variants'][0]['sku'])
        self.assertEqual(product2.barcode, LOYVERSE_ITEM_DATA['items'][1]['variants'][0]['barcode'])
        self.assertEqual(product2.sold_by_each, True)
        self.assertEqual(product2.is_bundle, False)
        self.assertEqual(product2.track_stock, True)
        self.assertEqual(product2.variant_count, 0)
        self.assertEqual(product2.is_variant_child, False)
        self.assertEqual(product2.show_product, True)
        self.assertEqual(product2.show_image, False)
        self.assertTrue(product2.reg_no > 100000)  # Check if we have a valid reg_no
        self.assertEqual((product2.created_date).strftime("%B, %d, %Y"), today)

        # Product 3
        product3 = products[2]

        self.assertEqual(product3.profile, self.profile1)
        self.assertEqual(product3.stores.all().count(), 6)
        self.assertEqual(product3.tax, None)
        self.assertEqual(product3.category, category1)
        self.assertEqual(product3.bundles.all().count(), 0)
        self.assertEqual(product3.modifiers.all().count(), 0)
        self.assertEqual(product3.image.url, f'/media/images/products/{product3.reg_no}_.jpg')
        self.assertEqual(product3.color_code, settings.DEFAULT_COLOR_CODE)
        self.assertEqual(product3.name, LOYVERSE_ITEM_DATA['items'][2]['item_name'])
        self.assertEqual(product3.cost, LOYVERSE_ITEM_DATA['items'][2]['variants'][0]['cost'])
        self.assertEqual(product3.price, Decimal('450.00'))
        self.assertEqual(product3.sku, LOYVERSE_ITEM_DATA['items'][2]['variants'][0]['sku'])
        self.assertEqual(product3.barcode, LOYVERSE_ITEM_DATA['items'][2]['variants'][0]['barcode'])
        self.assertEqual(product3.sold_by_each, True)
        self.assertEqual(product3.is_bundle, False)
        self.assertEqual(product3.track_stock, True)
        self.assertEqual(product3.variant_count, 0)
        self.assertEqual(product3.is_variant_child, False)
        self.assertEqual(product3.show_product, True)
        self.assertEqual(product3.show_image, False)
        self.assertTrue(product3.reg_no > 100000)  # Check if we have a valid reg_no
        self.assertEqual((product3.created_date).strftime("%B, %d, %Y"), today)

        # Product 4
        product4 = products[3]

        self.assertEqual(product4.profile, self.profile1)
        self.assertEqual(product4.stores.all().count(), 6)
        self.assertEqual(product4.tax, None)
        self.assertEqual(product4.category, None)
        self.assertEqual(product4.bundles.all().count(), 0)
        self.assertEqual(product4.modifiers.all().count(), 0)
        self.assertEqual(product4.image.url, f'/media/images/products/{product4.reg_no}_.jpg')
        self.assertEqual(product4.color_code, settings.DEFAULT_COLOR_CODE)
        self.assertEqual(product4.name, LOYVERSE_ITEM_DATA['items'][4]['item_name'])
        self.assertEqual(product4.cost, LOYVERSE_ITEM_DATA['items'][4]['variants'][0]['cost'])
        self.assertEqual(product4.price, Decimal('500.00'))
        self.assertEqual(product4.sku, LOYVERSE_ITEM_DATA['items'][4]['variants'][0]['sku'])
        self.assertEqual(product4.barcode, '')
        self.assertEqual(product4.sold_by_each, True)
        self.assertEqual(product4.is_bundle, False)
        self.assertEqual(product4.track_stock, True)
        self.assertEqual(product4.variant_count, 0)
        self.assertEqual(product4.is_variant_child, False)
        self.assertEqual(product4.show_product, True)
        self.assertEqual(product4.show_image, False)
        self.assertTrue(product4.reg_no > 100000)  # Check if we have a valid reg_no
        self.assertEqual((product4.created_date).strftime("%B, %d, %Y"), today)

        # Product 5
        product5 = products[4]

        self.assertEqual(product5.profile, self.profile1)
        self.assertEqual(product5.stores.all().count(), 6)
        self.assertEqual(product5.tax, None)
        self.assertEqual(product5.category, None)
        self.assertEqual(product5.bundles.all().count(), 0)
        self.assertEqual(product5.modifiers.all().count(), 0)
        self.assertEqual(product5.image.url, f'/media/images/products/{product5.reg_no}_.jpg')
        self.assertEqual(product5.color_code, settings.DEFAULT_COLOR_CODE)
        self.assertEqual(product5.name, LOYVERSE_ITEM_DATA['items'][5]['item_name'])
        self.assertEqual(product5.cost, LOYVERSE_ITEM_DATA['items'][5]['variants'][0]['cost'])
        self.assertEqual(product5.price, Decimal('750.00'))
        self.assertEqual(product5.sku, LOYVERSE_ITEM_DATA['items'][5]['variants'][0]['sku'])
        self.assertEqual(product5.barcode, '')
        self.assertEqual(product5.sold_by_each, True)
        self.assertEqual(product5.is_bundle, False)
        self.assertEqual(product5.track_stock, True)
        self.assertEqual(product5.variant_count, 0)
        self.assertEqual(product5.is_variant_child, False)
        self.assertEqual(product5.show_product, True)
        self.assertEqual(product5.show_image, False)
        self.assertTrue(product5.reg_no > 100000)  # Check if we have a valid reg_no
        self.assertEqual((product5.created_date).strftime("%B, %d, %Y"), today)

        # Product 6
        product6 = products[5]

        self.assertEqual(product6.profile, self.profile1)
        self.assertEqual(product6.stores.all().count(), 6)
        self.assertEqual(product6.tax, None)
        self.assertEqual(product6.category, None)
        self.assertEqual(product6.bundles.all().count(), 2)
        self.assertEqual(product6.modifiers.all().count(), 0)
        self.assertEqual(product6.image.url, f'/media/images/products/{product6.reg_no}_.jpg')
        self.assertEqual(product6.color_code, settings.DEFAULT_COLOR_CODE)
        self.assertEqual(product6.name, LOYVERSE_ITEM_DATA['items'][3]['item_name'])
        self.assertEqual(product6.cost, Decimal('0.00'))
        self.assertEqual(product6.price, Decimal('3000.00'))
        self.assertEqual(product6.sku, LOYVERSE_ITEM_DATA['items'][3]['variants'][0]['sku'])
        self.assertEqual(product6.barcode, '')
        self.assertEqual(product6.sold_by_each, True)
        self.assertEqual(product6.is_bundle, True)
        self.assertEqual(product6.track_stock, True)
        self.assertEqual(product6.variant_count, 0)
        self.assertEqual(product6.is_variant_child, False)
        self.assertEqual(product6.show_product, True)
        self.assertEqual(product6.show_image, False)
        self.assertTrue(product6.reg_no > 100000)  # Check if we have a valid reg_no
        self.assertEqual((product6.created_date).strftime("%B, %d, %Y"), today)

    def test_if_a_bundle_product_model_can_be_created_correctly(self):
        """
        Tests if bundles can be created and if bundles are the ones created last
        """

        # Create data
        self.call_sync_data(self.profile1)

        products = Product.objects.all().order_by('id')
        
        self.assertEqual(products.count(), 6)

        today = (timezone.now()).strftime("%B, %d, %Y")

        # Product 1
        product1 = products[0]
        product2 = products[4]

        # Product 6
        bundle_product = products[5]

        self.assertEqual(bundle_product.profile, self.profile1)
        self.assertEqual(bundle_product.stores.all().count(), 6)
        self.assertEqual(bundle_product.tax, None)
        self.assertEqual(bundle_product.category, None)
        self.assertEqual(bundle_product.bundles.all().count(), 2)
        self.assertEqual(bundle_product.modifiers.all().count(), 0)
        self.assertEqual(bundle_product.image.url, f'/media/images/products/{bundle_product.reg_no}_.jpg')
        self.assertEqual(bundle_product.color_code, settings.DEFAULT_COLOR_CODE)
        self.assertEqual(bundle_product.name, LOYVERSE_ITEM_DATA['items'][3]['item_name'])
        self.assertEqual(bundle_product.cost, Decimal('0.00'))
        self.assertEqual(bundle_product.price, Decimal('3000.00'))
        self.assertEqual(bundle_product.sku, LOYVERSE_ITEM_DATA['items'][3]['variants'][0]['sku'])
        self.assertEqual(bundle_product.barcode, '')
        self.assertEqual(bundle_product.sold_by_each, True)
        self.assertEqual(bundle_product.is_bundle, True)
        self.assertEqual(bundle_product.track_stock, True)
        self.assertEqual(bundle_product.variant_count, 0)
        self.assertEqual(bundle_product.is_variant_child, False)
        self.assertEqual(bundle_product.show_product, True)
        self.assertEqual(bundle_product.show_image, False)
        self.assertTrue(bundle_product.reg_no > 100000)  # Check if we have a valid reg_no
        self.assertEqual((bundle_product.created_date).strftime("%B, %d, %Y"), today)

        # Confirm bundles
        products = ProductBundle.objects.all().order_by('id')

        self.assertEqual(products.count(), 2)

        # Bundle 1
        bundle1 = ProductBundle.objects.get(product_bundle=product1)

        self.assertEqual(bundle1.product_bundle, product1)
        self.assertEqual(bundle1.quantity, 10)

        # Bundle 2
        bundle2 = ProductBundle.objects.get(product_bundle=product2)

        self.assertEqual(bundle2.product_bundle, product2)
        self.assertEqual(bundle2.quantity, 10)
    
    def test_if_product_models_and_stock_levels_are_assigned_correctly(self):
        """
        Tests if store avaialability and price are saved correctly
        """
        loyverse_item_data = copy.deepcopy(LOYVERSE_ITEM_DATA)

        # Create data
        self.call_sync_data(profile=self.profile1, loyverse_items_data=loyverse_item_data)

        products = Product.objects.all().order_by('id')
        stores = Store.objects.all().order_by('id')
        self.assertEqual(products.count(), 6)

        ############# Product 1 #############
        product1 = products[0]

        # Confirm stock levels were updated
        stock_levels = StockLevel.objects.filter(product=product1).order_by('id')
        self.assertEqual(stock_levels.count(), 6)


        ### Stock level units test are not icluded here since they have been
        # tested in the stock levels specific tests

        # Stock level 1
        self.assertEqual(stock_levels[0].store, stores[0])
        self.assertEqual(stock_levels[0].price, Decimal('300.00'))
        self.assertEqual(stock_levels[0].is_sellable, True)

        # Stock level 2
        self.assertEqual(stock_levels[1].store, stores[1])
        self.assertEqual(stock_levels[1].price, Decimal('300.00'))
        self.assertEqual(stock_levels[1].is_sellable, True)

        # Stock level 3
        self.assertEqual(stock_levels[2].store, stores[2])
        self.assertEqual(stock_levels[2].price, Decimal('300.00'))
        self.assertEqual(stock_levels[2].is_sellable, True)

        # Stock level 4
        self.assertEqual(stock_levels[3].store, stores[3])
        self.assertEqual(stock_levels[3].price, Decimal('300.00'))
        self.assertEqual(stock_levels[3].is_sellable, True)

        # Stock level 5
        self.assertEqual(stock_levels[4].store, stores[4])
        # self.assertEqual(stock_levels[4].units, Decimal('0.00'))
        self.assertEqual(stock_levels[4].price, Decimal('300.00'))
        self.assertEqual(stock_levels[4].is_sellable, True)

        # Stock level 6
        self.assertEqual(stock_levels[5].store, stores[5])
        # self.assertEqual(stock_levels[5].units, Decimal('0.00'))
        self.assertEqual(stock_levels[5].price, Decimal('300.00'))
        self.assertEqual(stock_levels[5].is_sellable, True)

        content = get_test_firebase_sender_log_content(only_include=['product'])

        pprint(content)
        print(len(content))

        print(product1.reg_no)

        result = {
            'payload': {
                'action_type': 'edit',
                'barcode': 'barcode',
                'category_data': '{}',
                'color_code': '#474A49',
                'cost': '0.0',
                'group_id': 'group_358728997492',
                'image_url': '/media/images/products/375395873806_.jpg',
                'is_bundle': 'False',
                'model': 'product',
                'modifier_data': '[]',
                'name': 'Shirt bundle',
                'reg_no': '375395873806',
                'relevant_stores': '[]',
                'show_image': 'False',
                'show_product': 'True',
                'sku': '10016',
                'sold_by_each': 'True',
                'stock_level': "{'units': '0.00', 'minimum_stock_level': '0', "
                                "'is_sellable': 'True', 'price': '470.00'}",
                'store_reg_no': '366343376407',
                'tax_data': '{}',
                'track_stock': 'True',
                'variant_count': '0',
                'variant_data': "{'options': [], 'variants': []}"
            }
        }

        self.assertEqual(stock_levels[5].is_sellable, True)
    '''

    def test_if_product_models_with_changes_are_sent_to_firebase(self):
        """
        Tests if store avaialability and price are saved correctly
        """
        loyverse_item_data = copy.deepcopy(LOYVERSE_ITEM_DATA)

        # Create data
        self.call_sync_data(profile=self.profile1, loyverse_items_data=loyverse_item_data)

        products = Product.objects.all().order_by('id')
        stores = Store.objects.all().order_by('id')
        self.assertEqual(products.count(), 6)

        ############# Product 1 #############
        product1 = products[0]

        # Confirm stock levels were updated
        stock_levels = StockLevel.objects.filter(product=product1).order_by('id')
        self.assertEqual(stock_levels.count(), 6)
        
        # Empty the log files
        empty_logfiles()

        # Make changes to the product and confirm if the changes are sent to firebase
        stock_level = stock_levels[0]
        stock_level.price = 611
        stock_level.save()

        # Create data
        self.call_sync_data(profile=self.profile1, loyverse_items_data=loyverse_item_data)

        content = get_test_firebase_sender_log_content(only_include=['product'])

        result1 = {
            'tokens': [], 
            'payload': {
                'group_id': self.profile1.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'product', 
                'action_type': 'edit', 

                'image_url': product1.get_image_url(),
                'color_code': product1.color_code,
                'name': product1.name,
                'cost': str(product1.cost),
                'sku': product1.sku,
                'barcode': product1.barcode,
                'sold_by_each': str(product1.sold_by_each),
                'is_bundle': str(product1.is_bundle),
                'track_stock': str(product1.track_stock),
                'variant_count': str(product1.variant_count),
                'show_product': str(product1.show_product),
                'show_image': str(product1.show_image),
                'reg_no': str(product1.reg_no),
                'stock_level': str(product1.get_store_stock_level_data(stores[0].reg_no)),
                'store_reg_no': str(stores[0].reg_no),
                'category_data': str(product1.get_category_data()),
                'tax_data': str(product1.get_tax_data()),
                'modifier_data': str(product1.get_modifier_list()),
                'variant_data': str(product1.get_variants_data_from_store(stores[0].reg_no)),
            }
        }

        self.assertEqual(content[0], result1)

    def test_if_product_models_with_no_changes_are_no_sent_to_firebase(self):
        """
        Tests if store avaialability and price are saved correctly
        """
        loyverse_item_data = copy.deepcopy(LOYVERSE_ITEM_DATA)

        # Create data
        self.call_sync_data(profile=self.profile1, loyverse_items_data=loyverse_item_data)

        products = Product.objects.all().order_by('id')
        stores = Store.objects.all().order_by('id')
        self.assertEqual(products.count(), 6)

        ############# Product 1 #############
        product1 = products[0]

        # Confirm stock levels were updated
        stock_levels = StockLevel.objects.filter(product=product1).order_by('id')
        self.assertEqual(stock_levels.count(), 6)
        
        # Empty the log files
        empty_logfiles()

        # Create data
        self.call_sync_data(profile=self.profile1, loyverse_items_data=loyverse_item_data)

        content = get_test_firebase_sender_log_content(only_include=['product'])

        self.assertEqual(content, [])

'''
    def test_if_product_models_are_assigned_stores_that_they_belong_to(self):
        """
        Tests if store avaialability and price are saved correctly
        """

        loyverse_item_data = copy.deepcopy(LOYVERSE_ITEM_DATA)

        loyverse_item_data['items'][0]['variants'][0]['stores'][0]['available_for_sale'] = False
        loyverse_item_data['items'][0]['variants'][0]['stores'][1]['price'] = 250
        

        # Create data
        self.call_sync_data(profile=self.profile1, loyverse_items_data=loyverse_item_data)

        products = Product.objects.all().order_by('id')
        stores = Store.objects.all().order_by('id')
        self.assertEqual(products.count(), 6)

        product1 = products[0]

        # Confirm stock levels were updated
        stock_levels = StockLevel.objects.filter(product=product1).order_by('id')
        self.assertEqual(stock_levels.count(), 6)


        ### Stock level units test are not icluded here since they have been
        # tested in the stock levels specific tests

        # Stock level 1
        self.assertEqual(stock_levels[0].store, stores[0])
        # self.assertEqual(stock_levels[0].units, Decimal('20.00'))
        self.assertEqual(stock_levels[0].price, Decimal('300.00'))
        self.assertEqual(stock_levels[0].is_sellable, True)

        # Stock level 2
        self.assertEqual(stock_levels[1].store, stores[1])
        # self.assertEqual(stock_levels[1].units, Decimal('20.00'))
        self.assertEqual(stock_levels[1].price, Decimal('300.00'))
        self.assertEqual(stock_levels[1].is_sellable, False)

        # Stock level 3
        self.assertEqual(stock_levels[2].store, stores[2])
        # self.assertEqual(stock_levels[2].units, Decimal('0.00'))
        self.assertEqual(stock_levels[2].price, Decimal('300.00'))
        self.assertEqual(stock_levels[2].is_sellable, True)

        # Stock level 4
        self.assertEqual(stock_levels[3].store, stores[3])
        # self.assertEqual(stock_levels[3].units, Decimal('0.00'))
        self.assertEqual(stock_levels[3].price, Decimal('300.00'))
        self.assertEqual(stock_levels[3].is_sellable, True)

        # Stock level 5
        self.assertEqual(stock_levels[4].store, stores[4])
        # self.assertEqual(stock_levels[4].units, Decimal('0.00'))
        self.assertEqual(stock_levels[4].price, Decimal('300.00'))
        self.assertEqual(stock_levels[4].is_sellable, True)

        # Stock level 6
        self.assertEqual(stock_levels[5].store, stores[5])
        # self.assertEqual(stock_levels[5].units, Decimal('0.00'))
        self.assertEqual(stock_levels[5].price, Decimal('300.00'))
        self.assertEqual(stock_levels[5].is_sellable, True)

    def test_if_store_models_were_created_correctly(self):

        # Create data
        # with self.assertNumQueries(25):
        self.call_sync_data(self.profile1)

        back_date = timezone.now() + datetime.timedelta(days=-1)
        back_date = back_date.strftime("%B, %d, %Y")

        stores = Store.objects.all().order_by('id')

        self.assertEqual(stores.count(), 6)

        for i in range(len(stores)):
            self.assertEqual(stores[i].name, LOYVERSE_STORE_DATA['stores'][i]['name'])
            self.assertEqual(str(stores[i].loyverse_store_id), LOYVERSE_STORE_DATA['stores'][i]['id'])

    def test_if_stores_cannot_be_duplicated_when_sync_data_has_been_called_twice(self):

        # Try to create data twice
        self.call_sync_data(self.profile1)
        self.call_sync_data(self.profile1)

        back_date = timezone.now() + datetime.timedelta(days=-1)
        back_date = back_date.strftime("%B, %d, %Y")

        stores = Store.objects.all().order_by('id')

        self.assertEqual(stores.count(), 6)
        self.assertEqual(stores.count(), len(LOYVERSE_STORE_DATA['stores']))
    
    def test_if_tax_models_were_created_correctly(self):
        # Create data
        # with self.assertNumQueries(25):
        self.call_sync_data(self.profile1)

        taxes = Tax.objects.all().order_by("id")
        self.assertEqual(taxes.count(), 4)


        # Tax 1
        tax1 = taxes[0]
        self.assertEqual(
            tax1.name,
            f"{LOYVERSE_TAX_DATA['taxes'][0]['name']} - {LOYVERSE_TAX_DATA['taxes'][0]['rate']}",
        )
        self.assertEqual(tax1.rate, LOYVERSE_TAX_DATA["taxes"][0]["rate"])
        self.assertEqual(str(tax1.loyverse_tax_id), LOYVERSE_TAX_DATA["taxes"][0]["id"])

        # Tax 2
        tax2 = taxes[1]
        self.assertEqual(
            tax2.name,
            f"{LOYVERSE_TAX_DATA['taxes'][1]['name']} - {LOYVERSE_TAX_DATA['taxes'][1]['rate']}",
        )
        self.assertEqual(tax2.rate, LOYVERSE_TAX_DATA["taxes"][1]["rate"])
        self.assertEqual(str(tax2.loyverse_tax_id), LOYVERSE_TAX_DATA["taxes"][1]["id"])

        # Tax 3
        tax3 = taxes[2]
        self.assertEqual(
            tax3.name,
            f"{LOYVERSE_TAX_DATA['taxes'][2]['name']} - {LOYVERSE_TAX_DATA['taxes'][2]['rate']}",
        )
        self.assertEqual(tax3.rate, LOYVERSE_TAX_DATA["taxes"][2]["rate"])
        self.assertEqual(str(tax3.loyverse_tax_id), LOYVERSE_TAX_DATA["taxes"][2]["id"])

        # Tax 4
        tax4 = taxes[3]
        self.assertEqual(
            tax4.name,
            f"{LOYVERSE_TAX_DATA['taxes'][3]['name']} - {LOYVERSE_TAX_DATA['taxes'][3]['rate']}",
        )
        self.assertEqual(tax4.rate, LOYVERSE_TAX_DATA["taxes"][3]["rate"])
        self.assertEqual(str(tax4.loyverse_tax_id), LOYVERSE_TAX_DATA["taxes"][3]["id"])

    def test_if_tax_models_can_be_updated_correctly(self):

        self.call_sync_data(self.profile1)

        ###### Confirm tax after it has been created 
        taxes = Tax.objects.all().order_by("id")

        # Tax 1
        tax1 = taxes[0]
        self.assertEqual(
            tax1.name,
            f"{LOYVERSE_TAX_DATA['taxes'][0]['name']} - {LOYVERSE_TAX_DATA['taxes'][0]['rate']}",
        )
        self.assertEqual(tax1.rate, LOYVERSE_TAX_DATA["taxes"][0]["rate"])
        self.assertEqual(str(tax1.loyverse_tax_id), LOYVERSE_TAX_DATA["taxes"][0]["id"])

        new_rate = 21.0
        loyverse_tax_data=copy.deepcopy(LOYVERSE_TAX_DATA)
        loyverse_tax_data['taxes'][0]['rate'] = new_rate

        # Create data
        # with self.assertNumQueries(25):
        self.call_sync_data(profile=self.profile1, loyverse_tax_data=loyverse_tax_data)

        taxes = Tax.objects.all().order_by("id")
        
        # Tax 1
        tax1 = taxes[0]
        self.assertEqual(
            tax1.name,
            f"{LOYVERSE_TAX_DATA['taxes'][0]['name']} - {new_rate}",
        )
        self.assertEqual(tax1.rate, new_rate)
        self.assertEqual(str(tax1.loyverse_tax_id), LOYVERSE_TAX_DATA["taxes"][0]["id"])

    def test_if_category_models_were_created_correctly(self):
        # Create data
        # with self.assertNumQueries(25):
        self.call_sync_data(self.profile1)

        categories = Category.objects.all().order_by("id")
        self.assertEqual(categories.count(), 12)

        # Category 1
        for i, category in enumerate(categories):

            category_name = LOYVERSE_CATEGORY_DATA['categories'][i]['name']
            category_id = LOYVERSE_CATEGORY_DATA['categories'][i]['id']

            self.assertEqual(category.name, category_name)
            self.assertEqual(str(category.loyverse_category_id), category_id)

    def test_if_category_models_can_be_updated_correctly(self):

        # Call sync data
        self.call_sync_data(self.profile1)

        categories = Category.objects.all().order_by("id")
        self.assertEqual(categories.count(), 12)

        # Confirm categoroy 
        category = categories[0]
        category_name = LOYVERSE_CATEGORY_DATA['categories'][0]['name']
        category_id = LOYVERSE_CATEGORY_DATA['categories'][0]['id']

        self.assertEqual(category.name, category_name)
        self.assertEqual(str(category.loyverse_category_id), category_id)

        # Update category name
        new_category_name = "New category"
        loyverse_category_data=copy.deepcopy(LOYVERSE_CATEGORY_DATA)
        loyverse_category_data['categories'][0]['name'] = new_category_name

        self.call_sync_data(profile=self.profile1, loyverse_category_data=loyverse_category_data)

        # Confirm if the change was successful
        categories = Category.objects.all().order_by("id")
        self.assertEqual(categories.count(), 12)

        category = categories[0]

        category_name = LOYVERSE_CATEGORY_DATA['categories'][0]['name']
        category_id = LOYVERSE_CATEGORY_DATA['categories'][0]['id']

        self.assertEqual(category.name, new_category_name)
        self.assertEqual(str(category.loyverse_category_id), category_id)

    def test_if_customer_models_can_be_created(self):

        self.call_sync_data(self.profile1)

        customers = Customer.objects.all().order_by('id')

        self.assertEqual(customers.count(), 3)

        self.assertEqual(customers[0].name, LOYVERSE_CUSTOMER_DATA['customers'][0]['name'])
        self.assertEqual(customers[0].email, LOYVERSE_CUSTOMER_DATA['customers'][0]['email'])
        self.assertEqual(str(customers[0].phone), LOYVERSE_CUSTOMER_DATA['customers'][0]['phone_number'])
        self.assertEqual(customers[0].customer_code, LOYVERSE_CUSTOMER_DATA['customers'][0]['customer_code'])
        self.assertEqual(str(customers[0].loyverse_customer_id), LOYVERSE_CUSTOMER_DATA['customers'][0]['id'])
        self.assertTrue(customers[0].reg_no > 100000)  # Check if we have a valid reg_no

        self.assertEqual(customers[1].name, LOYVERSE_CUSTOMER_DATA['customers'][1]['name'])
        self.assertEqual(customers[1].email, LOYVERSE_CUSTOMER_DATA['customers'][1]['email'])
        self.assertEqual(str(customers[1].phone), LOYVERSE_CUSTOMER_DATA['customers'][1]['phone_number'])
        self.assertEqual(customers[1].customer_code, LOYVERSE_CUSTOMER_DATA['customers'][1]['customer_code'])
        self.assertEqual(str(customers[1].loyverse_customer_id), LOYVERSE_CUSTOMER_DATA['customers'][1]['id'])
        self.assertTrue(customers[1].reg_no > 100000)  # Check if we have a valid reg_no

        self.assertEqual(customers[2].name, LOYVERSE_CUSTOMER_DATA['customers'][2]['name'])
        self.assertEqual(customers[2].email, LOYVERSE_CUSTOMER_DATA['customers'][2]['email'])
        self.assertEqual(str(customers[2].phone), LOYVERSE_CUSTOMER_DATA['customers'][2]['phone_number'])
        self.assertEqual(customers[2].customer_code, LOYVERSE_CUSTOMER_DATA['customers'][2]['customer_code'])
        self.assertEqual(str(customers[2].loyverse_customer_id), LOYVERSE_CUSTOMER_DATA['customers'][2]['id'])
        self.assertTrue(customers[2].reg_no > 100000)  # Check if we have a valid reg_no

    def test_if_customer_cant_be_dublicated(self):

        # Call sync data twice
        self.call_sync_data(self.profile1)
        self.call_sync_data(self.profile1)

        customers = Customer.objects.all().order_by("id")
        self.assertEqual(customers.count(), 3)
   

    def test_if_LoyverseSyncData_can_handle_being_passed_None_values(self):

        LoyverseSyncData(
            profile=self.profile1,
            stores=None,
            employees=None,
            taxes=None,
            categories=None,
            customers=None,
            items=None,
            levels=None
        ).sync_data()
'''