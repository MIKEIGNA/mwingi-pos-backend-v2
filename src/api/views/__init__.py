from .accounts.login_views import*
from .accounts.password_views import*
from .accounts.email_views import*
from .accounts.hijack_views import*

from .profiles.role_veiws import*
from .profiles.tp_profile_views import*
from .profiles.tp_employee_profile_views import*

from .profiles.employee_profile_views import*
from .profiles.mg_employee_profile_views import*

from .profiles.tp_customer_views import *
from .profiles.tp_customer_pos_views import*
from .profiles.ep_customer_views import*
from .profiles.ep_customer_pos_views import*

from .profiles.user_settings_views import*

from .stores.tp_store_views import*
from .stores.ep_store_views import*

from .stores.tp_tax_views import*
from .stores.tp_tax_pos_views import*
from .stores.ep_tax_views import*
from .stores.ep_tax_pos_views import*

from .stores.tp_discount_views import*
from .stores.tp_discount_pos_views import*
from .stores.ep_discount_views import*
from .stores.ep_discount_pos_views import*


from .stores.tp_category_views import*
from .stores.ep_category_views import*


from .products.product_views import*
from .products.ep_product_views import*
from .products.product_pos_views import*
from .products.modifier_views import*
from .products.ep_modifier_views import*
from .products.modifier_pos_views import*

from .products.ep_product_pos_views import*
from .products.ep_modifier_pos_views import*

from .firebase.views import*

from .sales.receipt_views import*
from .sales.invoice_views import*

from .sales.receipt_pos_views import*

from .inventories.supplier_views import*
from .inventories.stock_adjustment_views import*
from .inventories.transfer_order_views import*
from .inventories.inventory_count_views import*
from .inventories.purchase_order_views import*
from .inventories.inventory_valuation_views import*
from .inventories.inventory_history_views import*
from .inventories.product_transform_views import*

from .reports.tp_report_views import*
from .reports.ep_report_views import*

from .clusters.views import*

from .loyverse.views import*
from .webhooks.views import*

from .integrations.tims_views import*