import threading
from django.test import TransactionTestCase
from core.models import Seller, TopUpRequest, TopUpAlreadyAppliedError


# race condition / concurrency test
class TopUpConcurrencyTest(TransactionTestCase):
    reset_sequences = True  # ensures IDs are predictable

    def setUp(self):
        self.seller = Seller.objects.create(name="Seller1", balance=0)
        self.topup = TopUpRequest.objects.create(seller=self.seller, amount=100)
        self.success_count = 0
        self.lock = threading.Lock()  # برای ایمن کردن self.success_count
        print("\n[SETUP] Seller created with balance=0 and one TopUpRequest(amount=100)")

    def apply_topup(self, index):
        try:
            from django.db import transaction
            with transaction.atomic():
                self.topup.apply(approver=f"thread-{index}")
                with self.lock:
                    self.success_count += 1
                print(f"[THREAD {index}] Successfully applied topup")
        except TopUpAlreadyAppliedError:
            print(f"[THREAD {index}] TopUpAlreadyAppliedError (ignored)")

    def test_concurrent_topup_apply(self):
        print("[TEST] Starting concurrent topup apply with 5 threads...")

        threads = [threading.Thread(target=self.apply_topup, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # دوباره از DB بارگذاری
        self.seller.refresh_from_db()
        print(f"[RESULT] Seller balance after concurrent apply: {self.seller.balance}")
        print(f"[RESULT] Success count (should be 1): {self.success_count}")

        self.assertEqual(self.seller.balance, 100)
        self.assertEqual(self.success_count, 1, "TopUp should only apply once")
# docker-compose exec django python manage.py test core.tests.test_topup_concurrent --keepdb -v 2 --debug-mode