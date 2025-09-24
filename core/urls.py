from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SellerViewSet, TransactionViewSet, TopUpRequestViewSet, sell_charge_api

router = DefaultRouter()
router.register(r"sellers", SellerViewSet, basename="seller")
router.register(r"transactions", TransactionViewSet, basename="transaction")
router.register(r"topups", TopUpRequestViewSet, basename="topup")

urlpatterns = [
    path("", include(router.urls)),
    path("sell_charge/", sell_charge_api, name="sell-charge"),
]
