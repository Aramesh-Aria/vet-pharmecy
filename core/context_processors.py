"""Site-chrome context: data the global header/footer need on every page.

The header renders an animal-category menu (ADR-0006) and a cart badge, so the
active categories and the signed-in owner's cart count must be available to
``base.html`` everywhere — not just on views that happen to pass them.
"""
from catalog.models import AnimalCategory
from pharmacy.models import Cart


def site_chrome(request):
    categories = AnimalCategory.objects.filter(is_active=True)

    cart_count = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(owner=request.user).first()
        if cart is not None:
            cart_count = cart.item_count

    return {"nav_categories": categories, "cart_count": cart_count}
