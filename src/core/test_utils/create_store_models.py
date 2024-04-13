import uuid
from django.utils import timezone

from core.time_utils.time_localizers import utc_to_local_datetime

from stores.models import Store, Tax, Category, Discount

# ------------- Store -------------
def create_new_store(
        profile,
        name,
        created_date=utc_to_local_datetime(timezone.now())
    ):

    model = Store.objects.create(
        profile=profile,
        name=name,
        address="Nairobi",
        created_date=created_date,
        loyverse_store_id=uuid.uuid4()
    )

    return model

# ------------- Tax -------------
def create_new_tax(
        profile,
        store,
        name,
        rate=20.05,
        created_date=utc_to_local_datetime(timezone.now())
    ):

    model = Tax.objects.create(
        profile=profile,
        name=name,
        rate=rate,
        created_date=created_date
    )

    model.stores.add(store)

    return model



# ------------- Category -------------
def create_new_category(
        profile,
        name,
        created_date=utc_to_local_datetime(timezone.now())
    ):

    model = Category.objects.create(
        profile=profile,
        name=name,
        created_date=created_date
    )

    return model


# ------------- Discount -------------
def create_new_discount(
        profile,
        store,
        name,
        value=20.05,
        amount=50.05,
        created_date=utc_to_local_datetime(timezone.now())
    ):

    model = Discount.objects.create(
        profile=profile,
        name=name,
        value=value,
        amount=amount,
        created_date=created_date
    )

    model.stores.add(store)

    return model
