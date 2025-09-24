from django.test import TestCase
from decimal import Decimal
from core.models import Seller, sell_charge
import concurrent.futures

class SellChargeTests(TestCase):
    def setUp(self):
        # یک فروشنده با موجودی کافی
        self.seller1 = Seller.objects.create(name="Seller 1", balance=50000)
        self.seller2 = Seller.objects.create(name="Seller 2", balance=50000)

    def test_simple_sales(self):
        # ۵۰۰ فروش شارژ برای هر فروشنده
        for i in range(500):
            sell_charge(self.seller1.id, f"0912000{i}", 5)
            sell_charge(self.seller2.id, f"0912100{i}", 5)

        self.seller1.refresh_from_db()
        self.seller2.refresh_from_db()
        assert self.seller1.balance == Decimal(50000 - 2500)
        assert self.seller2.balance == Decimal(50000 - 2500)

    def test_parallel_sales_thread(self):
        # تست موازی با thread
        def sell_task(seller_id, phone_number, amount):
            sell_charge(seller_id, phone_number, amount)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(sell_task, self.seller1.id, f"0912000{i}", 5)
                for i in range(10000)
            ]
            concurrent.futures.wait(futures)

        self.seller1.refresh_from_db()
        print("Final balance after parallel sales:", self.seller1.balance)
