from .models import ShopOwner, Customer

# ---------- Customer Context ----------
def customer_data(request):
    customer = None

    if request.session.get('customer_id'):
        customer = Customer.objects.filter(
            id=request.session['customer_id']
        ).first()

    return {
        'customer': customer
    }
