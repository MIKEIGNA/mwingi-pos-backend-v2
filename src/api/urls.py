from rest_framework.urlpatterns import format_suffix_patterns

from .api_urls.accounts_urls import account_url_patterns
from .api_urls.firebase_urls import firebase_url_patterns
from .api_urls.products_urls import product_url_patterns
from .api_urls.profiles_urls import profile_url_patterns
from .api_urls.stores_urls import store_url_patterns
from .api_urls.sales_urls import sales_url_patterns
from .api_urls.inventories_urls import inventory_url_patterns
from .api_urls.reports_urls import reports_url_patterns
from .api_urls.clusters_urls import cluster_url_patterns
from .api_urls.loyverse_urls import loyverse_url_patterns
from .api_urls.webhooks_urls import webhook_url_patterns
from .api_urls.integrations_urls import integrations_url_patterns

app_name = 'api'
urlpatterns = []

urlpatterns += account_url_patterns
urlpatterns += firebase_url_patterns
urlpatterns += product_url_patterns
urlpatterns += profile_url_patterns
urlpatterns += store_url_patterns
urlpatterns += sales_url_patterns
urlpatterns += inventory_url_patterns
urlpatterns += reports_url_patterns
urlpatterns += cluster_url_patterns
urlpatterns += loyverse_url_patterns
urlpatterns += webhook_url_patterns
urlpatterns += integrations_url_patterns

urlpatterns = format_suffix_patterns(urlpatterns)