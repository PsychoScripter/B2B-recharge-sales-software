from rest_framework import serializers
from .models import Seller, PhoneNumber, Transaction, TopUpRequest


class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = ["id", "name", "balance", "version", "created_at"]
        read_only_fields = ["balance", "version", "created_at"]


class PhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneNumber
        fields = ["id", "number", "created_at"]


class TransactionSerializer(serializers.ModelSerializer):
    seller = serializers.PrimaryKeyRelatedField(read_only=True)
    phone = PhoneNumberSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "seller",
            "tx_type",
            "amount",
            "balance_after",
            "phone",
            "reference",
            "metadata",
            "created_at",
        ]


class TopUpRequestSerializer(serializers.ModelSerializer):
    seller = serializers.PrimaryKeyRelatedField(queryset=Seller.objects.all())
    idempotency_key = serializers.CharField(required=False)  # ← اینجا تغییر

    class Meta:
        model = TopUpRequest
        fields = [
            "id",
            "seller",
            "amount",
            "idempotency_key",
            "approved",
            "applied_at",
            "approved_by",
            "notes",
            "created_at",
        ]
        read_only_fields = ["approved", "applied_at", "approved_by", "created_at"]


class SellChargeSerializer(serializers.Serializer):
    """برای endpoint فروش شارژ"""

    seller_id = serializers.IntegerField()
    phone_number = serializers.CharField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=0)
    reference = serializers.CharField(required=False)
    metadata = serializers.JSONField(required=False)

    def validate_phone_number(self, value):
        if not PhoneNumber.objects.filter(number=value).exists():
            raise serializers.ValidationError("Phone number does not exist")
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("amount must be > 0")
        return value
