from django.test import TestCase
from decimal import Decimal
from core.models import Seller
from core.tasks import sell_charge_task
from celery import group
from celery.result import AsyncResult, allow_join_result
import time

class SellChargeAsyncTests(TestCase):
    def setUp(self):
        self.seller1 = Seller.objects.create(name="Seller 1", balance=50000)
        self.seller2 = Seller.objects.create(name="Seller 2", balance=50000)

    def test_parallel_sales_celery_real(self):
        num_sales = 100
        tasks = [sell_charge_task.s(self.seller1.id, f"0912{i:03}", 5) for i in range(num_sales)]

        from celery import group
        job = group(tasks)
        result = job.apply_async()

        from celery.result import allow_join_result
        with allow_join_result():
            result.join(timeout=120)  # max 2 دقیقه

        # refresh موجودی
        self.seller1.refresh_from_db()
        print("Final balance after Celery parallel sales:", self.seller1.balance)

        # بررسی موجودی
        expected_balance = Decimal(50000 - 5*num_sales)
        self.assertEqual(self.seller1.balance, expected_balance)
