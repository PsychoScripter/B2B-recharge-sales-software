import uuid
from sqlite3 import IntegrityError

from django.db import models
from django.core.validators import MinValueValidator

try:
    from django.db.models import JSONField
except ImportError:
    from django.contrib.postgres.fields import JSONField


class InsufficientBalanceError(Exception):
    pass


class TopUpAlreadyAppliedError(Exception):
    pass


class Seller(models.Model):
    name = models.CharField(max_length=200)
    balance = models.DecimalField(
        max_digits=18, decimal_places=0, default=0,
        validators=[MinValueValidator(0)]
    )
    version = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(balance__gte=0), name="seller_balance_non_negative"),
        ]

    def __str__(self):
        return f"Seller(id={self.pk}, name={self.name}, balance={self.balance})"


class PhoneNumber(models.Model):
    number = models.CharField(max_length=32, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_charged_at = models.DateTimeField(null=True, blank=True)  # 👈 اضافه شد

    def __str__(self):
        return self.number


class Transaction(models.Model):
    TOPUP = "TOPUP"
    SALE = "SALE"   # 👈 استفاده برای فروش شارژ
    ADJUST = "ADJUST"
    TX_TYPES = [(TOPUP, "Topup"), (SALE, "Sale"), (ADJUST, "Adjust")]

    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name="transactions")
    tx_type = models.CharField(max_length=10, choices=TX_TYPES)
    amount = models.DecimalField(max_digits=18, decimal_places=0)
    balance_after = models.DecimalField(max_digits=18, decimal_places=0)
    phone = models.ForeignKey(PhoneNumber, null=True, blank=True, on_delete=models.SET_NULL)
    reference = models.CharField(max_length=255, null=True, blank=True)
    metadata = JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["seller", "created_at"])]

    def __str__(self):
        return f"TX({self.pk}) {self.tx_type} {self.amount} seller={self.seller_id} after={self.balance_after}"


class TopUpRequest(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name="topup_requests")
    amount = models.DecimalField(max_digits=18, decimal_places=0, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    idempotency_key = models.CharField(max_length=255, unique=True, blank=True, editable=False)
    approved = models.BooleanField(default=False)
    applied_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.CharField(max_length=200, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"TopUpRequest({self.pk}) seller={self.seller_id} amount={self.amount} applied={bool(self.applied_at)}"

    def save(self, *args, **kwargs):
        if not self.idempotency_key:  # اگر دستی ست نشده باشه
            self.idempotency_key = str(uuid.uuid4())
        super().save(*args, **kwargs)

    @classmethod
    def create_idempotent(cls, seller, amount, idempotency_key=None, **kwargs):
        if idempotency_key is None:
            idempotency_key = str(uuid.uuid4())
        obj, created = cls.objects.get_or_create(
            idempotency_key=idempotency_key,
            defaults={"seller": seller, "amount": amount, **kwargs},
        )
        return obj, created

    def apply(self, approver=None):
        """Apply top-up requests atomically and safely."""
        with transaction.atomic():
            # Lock request and seller
            tr = TopUpRequest.objects.select_for_update().select_related("seller").get(pk=self.pk)
            seller = tr.seller

            if tr.applied_at:
                raise TopUpAlreadyAppliedError("TopUp already applied")

            # Update seller balance directly
            seller.balance += tr.amount
            seller.version += 1
            seller.save(update_fields=["balance", "version"])

            # Create transaction log
            Transaction.objects.create(
                seller=seller,
                tx_type=Transaction.TOPUP,
                amount=tr.amount,
                balance_after=seller.balance,
                reference=f"topup:{tr.idempotency_key}",
                metadata={"applied_by": approver} if approver else None
            )

            # Mark request as applied
            tr.applied_at = timezone.now()
            tr.approved = True
            tr.approved_by = approver if approver else tr.approved_by
            tr.save(update_fields=["applied_at", "approved", "approved_by"])

            return seller.balance


from django.utils import timezone
from django.db import transaction
from django.db.models import F
from decimal import Decimal


def sell_charge(seller_id: int, phone_number: str, amount: Decimal, reference: str = None, metadata: dict = None):
    """Deduct the amount from the seller's account and record the sales transaction atomically."""
    amount = Decimal(amount)
    if amount <= 0:
        raise ValueError("Amount must be positive")

    with transaction.atomic():
        # Lock seller
        seller = Seller.objects.select_for_update().get(pk=seller_id)
        if seller.balance < amount:
            raise InsufficientBalanceError("Insufficient balance")

        # Deduct balance
        seller.balance -= amount
        seller.version += 1
        seller.save(update_fields=["balance", "version"])

        # Get or create phone safely
        try:
            phone_obj, _ = PhoneNumber.objects.get_or_create(number=phone_number)
        except IntegrityError:
            phone_obj = PhoneNumber.objects.select_for_update().get(number=phone_number)

        # Merge metadata
        tx_metadata = {"phone_number": phone_number}
        if metadata:
            tx_metadata.update(metadata)

        # Ensure idempotency
        if reference:
            tx, created = Transaction.objects.get_or_create(
                reference=reference,
                defaults={
                    "seller": seller,
                    "tx_type": Transaction.SALE,
                    "amount": -amount,
                    "balance_after": seller.balance,
                    "phone": phone_obj,
                    "metadata": tx_metadata
                }
            )
            if not created:
                return seller.balance
        else:
            Transaction.objects.create(
                seller=seller,
                tx_type=Transaction.SALE,
                amount=-amount,
                balance_after=seller.balance,
                phone=phone_obj,
                reference=f"sale:{phone_number}:{timezone.now().timestamp()}",
                metadata=tx_metadata
            )

        # Update last charged timestamp
        phone_obj.last_charged_at = timezone.now()
        phone_obj.save(update_fields=["last_charged_at"])

        return seller.balance

