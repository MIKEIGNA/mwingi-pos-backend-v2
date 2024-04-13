from django.utils import timezone
from core.time_utils.time_localizers import utc_to_local_datetime
from products.models import Product


def create_new_product(
        profile,
        store=None,
        tax=None,
        category=None,
        name="UnNamed",
        track_stock=True,
        created_date=utc_to_local_datetime(timezone.now())
    ):
    
    model = Product.objects.create(
        profile=profile,
        tax=tax,
        category=category,
        name=name,
        price=2500,
        cost=1000,
        sku='sku1',
        barcode='code123',
        track_stock=track_stock,
        created_date=created_date
    )

    if store:
        model.stores.add(store)

    return model
