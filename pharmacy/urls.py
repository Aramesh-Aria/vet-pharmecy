from django.urls import path

from . import views

app_name = "pharmacy"

urlpatterns = [
    # Cart
    path("cart/", views.CartView.as_view(), name="cart"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/update/<int:product_id>/", views.cart_update, name="cart_update"),
    path("cart/remove/<int:product_id>/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    # Orders
    path("orders/", views.OrderListView.as_view(), name="order_list"),
    path("orders/<int:pk>/", views.OrderDetailView.as_view(), name="order_detail"),
    # Prescriptions & refills
    path("prescriptions/", views.PrescriptionListView.as_view(), name="prescriptions"),
    path("prescriptions/<int:prescription_id>/order/", views.prescription_add_to_cart, name="prescription_add"),
    path("refill/<int:prescription_id>/", views.refill_request, name="refill_request"),
    path("refills/", views.RefillListView.as_view(), name="refill_list"),
    path("refills/<int:pk>/", views.RefillDetailView.as_view(), name="refill_detail"),
]
