import threading
from django.test import TransactionTestCase
from core.models import Seller, TopUpRequest, TopUpAlreadyAppliedError

class TopUpConcurrencyTest(TransactionTestCase):
    reset_sequences = True  # ensures IDs are predictable

    def setUp(self):
        self.seller = Seller.objects.create(name="Seller1", balance=0)
        self.topup = TopUpRequest.objects.create(seller=self.seller, amount=100)
        self.success_count = 0
        self.lock = threading.Lock()  # برای ایمن کردن self.success_count

    def apply_topup(self, index):
        try:
            # هر thread خودش تراکنش atomic می‌سازه
            from django.db import transaction
            with transaction.atomic():
                self.topup.apply(approver=f"thread-{index}")
                with self.lock:
                    self.success_count += 1
        except TopUpAlreadyAppliedError:
            pass

    def test_concurrent_topup_apply(self):
        threads = [threading.Thread(target=self.apply_topup, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # دوباره از DB بارگذاری
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.balance, 100)
        self.assertEqual(self.success_count, 1, "TopUp should only apply once")


# docker-compose exec django python manage.py test core.tests.test_topup_concurrent.TopUpConcurrencyTest --keepdb