from celery import shared_task
from .models import sell_charge, InsufficientBalanceError

@shared_task(bind=True, max_retries=3)
def sell_charge_task(self, seller_id, phone_number, amount, reference=None, metadata=None):
    try:
        new_balance = sell_charge(seller_id, phone_number, amount, reference, metadata)
        return {"seller_id": seller_id, "new_balance": float(new_balance)}
    except InsufficientBalanceError:
        return {"seller_id": seller_id, "error": "Insufficient balance"}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)
