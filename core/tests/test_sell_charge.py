from django.test import TestCase
from decimal import Decimal
from core.models import Seller, TopUpRequest

class TopUpTests(TestCase):
    def setUp(self):
        self.seller1 = Seller.objects.create(name="Seller 1", balance=0)
        self.seller2 = Seller.objects.create(name="Seller 2", balance=0)

    def test_topup_apply(self):
        # ایجاد و اعمال ۱۰ top-up
        for i in range(5):
            TopUpRequest.objects.create(
                seller=self.seller1, amount=10000, idempotency_key=f"s1-{i}"
            ).apply()
            TopUpRequest.objects.create(
                seller=self.seller2, amount=10000, idempotency_key=f"s2-{i}"
            ).apply()

        self.seller1.refresh_from_db()
        self.seller2.refresh_from_db()

        # بررسی موجودی نهایی
        assert self.seller1.balance == Decimal(50000)
        assert self.seller2.balance == Decimal(50000)
