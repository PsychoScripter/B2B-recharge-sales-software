from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from .models import Seller, TopUpRequest, Transaction, sell_charge, InsufficientBalanceError, TopUpAlreadyAppliedError
from .serializers import SellerSerializer, TopUpRequestSerializer, TransactionSerializer, SellChargeSerializer
from .tasks import sell_charge_task

# Seller CRUD
class SellerViewSet(viewsets.ModelViewSet):
    queryset = Seller.objects.all().order_by("id")
    serializer_class = SellerSerializer

class TransactionPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

# Transaction فقط Read
class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["seller", "tx_type"]
    pagination_class = TransactionPagination

    def get_queryset(self):
        return Transaction.objects.all().order_by("-created_at")


# TopUpRequest
class TopUpRequestViewSet(viewsets.ModelViewSet):
    queryset = TopUpRequest.objects.all().order_by("-created_at")
    serializer_class = TopUpRequestSerializer

    @action(detail=True, methods=["post"])
    def apply(self, request, pk=None):
        topup = self.get_object()
        approver = request.user.username if request.user.is_authenticated else None
        try:
            new_balance = topup.apply(approver=approver)
        except TopUpAlreadyAppliedError:
            return Response({"detail": "Already applied"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "status": "applied",
            "seller_id": topup.seller.id,
            "new_balance": new_balance,
        })


# فروش شارژ با Celery
@api_view(["POST"])
def sell_charge_api(request):
    serializer = SellChargeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    seller_id = serializer.validated_data["seller_id"]
    phone_number = serializer.validated_data["phone_number"]
    amount = serializer.validated_data["amount"]
    reference = serializer.validated_data.get("reference")
    metadata = serializer.validated_data.get("metadata")

    # اجرای async با Celery
    task = sell_charge_task.delay(seller_id, phone_number, amount, reference, metadata)

    return Response({"status": "queued", "task_id": task.id}, status=202)
