from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from decimal import Decimal
from django.http import JsonResponse
from django.utils import timezone 
from django.db.models.functions import TruncDate , TruncMonth
from collections import Counter
from django.conf import settings
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import uuid
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib.auth.decorators import login_required
from .utils import is_under_warranty
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from datetime import date
from django.db.models import Sum , Count 
from django.db import transaction
from .models import ShopInfo,ShopOwner, Product, Customer, ShopPurProd, Category ,Service , Invoice , InvoiceItem , Notification ,ServiceRequest, ServiceInvoice
from django.http import HttpResponse
from .forms import ProductForm , ProdCategory , ProdService , ShopOwnerProfile , SellProductForm ,ServiceRequestForm
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from django.http import HttpResponse
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from weasyprint import HTML
from django.template.loader import render_to_string
from django.views.decorators.cache import never_cache


# ---------- Shop Owner Registration ----------

def register(request):
    if request.method == "POST":
        role = request.POST.get("role")

        if role == "shop_owner":
            username = request.POST.get("sw_uname")
            email = request.POST.get("email")

            if ShopOwner.objects.filter(sw_uname=username).exists():
                messages.error(request, "Username already exists")
                return redirect("register")

            if ShopOwner.objects.filter(email=email).exists():
                messages.error(request, "Email already exists")
                return redirect("register")
            ShopOwner.objects.create(
                sw_uname=request.POST.get("sw_uname"),
                email=request.POST.get("email"),
                password=make_password(request.POST.get("password")),
                address=request.POST.get("address"),
                phone_no=request.POST.get("phone_no"),
            )
            messages.success(request, "Shop Owner registered successfully")
            return redirect("login")

        elif role == "customer":
            username = request.POST.get("c_username")

            if Customer.objects.filter(u_name=username).exists():
                messages.error(request, "Username already exists")
                return redirect("register")

            Customer.objects.create(
                u_name=username,
                email=request.POST.get("c_email"),
                password=make_password(request.POST.get("c_password")),
                phone_no=request.POST.get("c_phone"),
                address=request.POST.get("c_address"),
            )

            messages.success(request, "Customer registered successfully")
            return redirect("login")

        else:
            messages.error(request, "Please select a role")

    return render(request, 'core/ShopRegister.html', {
    'selected_role': request.POST.get('role', 'customer'),
    'sw_uname': request.POST.get('sw_uname', ''),
    'c_uname': request.POST.get('c_uname', ''),
})

def services(request):
    services = Service.objects.all()
    return render(request, 'core/home_service.html', {'services': services})

def about(request):
    shop = ShopInfo.objects.first()
    return render(request,'core/about.html',{'shop':shop})

def bookservice(request):
    messages.warning(request, "Please login first to book a service")
    return redirect('login')


# ---------- Shop Owner Login ----------
def shop_login(request):
    if request.method == "POST":
        role = request.POST.get("role")

        if role == "shop_owner":
            sh_uname = request.POST.get('sw_uname', '').strip()
            password = request.POST.get('password', '').strip()
            try:
                owner = ShopOwner.objects.get(sw_uname=sh_uname)
            
                emails = ShopOwner.objects.values_list('email', flat=True)
                print([email for email, count in Counter(emails).items() if count > 1])
                if owner.check_password(password):
                    request.session['shopowner_id'] = owner.sw_id
                    messages.success(request, "Login successfully!")  # Success message
                    return redirect('shop_analysis')  # Redirect to dashboard only if valid
                else:
                    messages.error(request, "Invalid password")
            except ShopOwner.DoesNotExist:
                messages.error(request, "Shop owner not found")
        elif role == "customer":
            c_uname = request.POST.get('u_name', '').strip()

            password = request.POST.get('c_password', '').strip()
            try:
                cust = Customer.objects.get(u_name=c_uname)
            
                emails = Customer.objects.values_list('email', flat=True)
                print([email for email, count in Counter(emails).items() if count > 1])
                if cust.check_password(password):
                    request.session['customer_id'] = cust.c_id
                    messages.success(request, "Login successfully!")  # Success message
                    return redirect('customer_dashboard')  # Redirect to dashboard only if valid
                else:
                    messages.error(request, "Invalid password")
            except Customer.DoesNotExist:
                messages.error(request, "Customer not found")
        else :
            messages.error(request, "Register First")
            
    return render(request, 'core/ShopLogin.html', {
    'selected_role': request.POST.get('role', 'customer'),
    'sw_uname': request.POST.get('sw_uname', ''),
    'u_name': request.POST.get('u_name', ''),  # match template variable
})

def register_view(request):
    return render(request, "core/ShopRegister.html")

def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            owner = ShopOwner.objects.get(email=email)
            token = uuid.uuid4()
            owner.reset_token = token
            owner.save()

            reset_link = f"http://127.0.0.1:8000/reset-password/{token}/"

            send_mail(
                "Password Reset",
                f"Click link to reset password:\n{reset_link}",
                settings.EMAIL_HOST_USER,
                [email],
            )

            messages.success(request, "Reset link sent to your email.")
        except ShopOwner.DoesNotExist:
            messages.error(request, "Email not found")

    return render(request, "core/register/password_reset.html")

def reset_password(request, token):
    try:
        owner = ShopOwner.objects.get(reset_token=token)
    except ShopOwner.DoesNotExist:
        messages.error(request, "Invalid or expired link")
        return redirect("login")

    if request.method == "POST":
        new_password = request.POST.get("password")
        owner.password = make_password(new_password)  # later we’ll hash it
        owner.reset_token = None
        owner.save()

        messages.success(request, "Password reset successful")
        return redirect("login")

    return render(request, "core/register/reset_password.html")

def shopowner_profile(request):
    if 'shopowner_id' not in request.session:
        messages.error(request, "Please login first")
        return redirect('login')

    owner = get_object_or_404(
        ShopOwner, sw_id=request.session['shopowner_id']
    )

    if request.method == 'POST':
        form = ShopOwnerProfile(request.POST, instance=owner)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully")
            return redirect('ow_detail')
    else:
        form = ShopOwnerProfile(instance=owner)

    return render(request, 'core/owner/owner_profile.html', {'form': form})


# ---------- Dashboard ----------
def shop_dashboard(request):
    if 'shopowner_id' not in request.session:
        messages.error(request, "You must login first.")
        return redirect("login")

    total_products = Product.objects.count()
    total_sales = ShopPurProd.objects.count()
    total_customers = Customer.objects.count()
    available_stock = Product.objects.aggregate(
        total_stock=Sum('stock')
    )['total_stock'] or 0

    context = {
        'total_products': total_products,
        'total_sales': total_sales,
        'total_customers': total_customers,
        'available_stock': available_stock
    }

    return render(request, 'core/owner/ShopDash.html', context)



def shopowner_context(request):
    owner = None
    if request.session.get('shopowner_id'):
        owner = ShopOwner.objects.filter(
            sw_id=request.session['shopowner_id']
        ).first()

    return {
        'shopowner': owner
    }
    
# ---------- Logout ----------

def shopowner_logout(request):
    if 'shopowner_id' in request.session:
        request.session.pop('shopowner_id', None)
    messages.success(request, "Logged out successfully")
    return redirect('login')



# ---------- Simple Home View ----------
def home(request):
    return render(request, 'core/owner/home.html')



def role_reg(request, role):
    # role will be either "ShopOwner" or "Customer"
    if role == "ShopOwner":
        template = "core/ShopLogin.html"
    elif role == "Customer":
        template = "#"
    else:
        template = "core/ShopRegister.html"  # fallback

    return render(request, template, {"role": role})

    
            
# ---------- Product Management ----------
def manage_products(request):
    products = Product.objects.all()
    return render(request, "core/owner/manage_product.html", {'products': products})


# def product_list(request):
#     products = Product.objects.select_related().all()
#     return render(request,"core/S_Owner/product_list.html",{'products':products})


def productAdd(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Product Added..!")
            return redirect('manage_prod')
        
    else:
        form = ProductForm()
    return render(request,'core/owner/product_add.html', {'form': form, 'title': 'Add Product'})


def update_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request,"Updated successfully")
            return redirect('manage_prod')
    
    return render(request,'core/owner/update_product.html',{'form':form,'title':'Edit Product'})


def delete_prod(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        messages.success(request,"Product deleted successfully")
        return redirect('manage_prod')
    
    return render(request , 'core/owner/delete_conf.html',{'product':product})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'core/owner/product_detail.html', {'product': product})


def analysis(request):

    # 1️⃣ Total products
    total_products = Product.objects.count()

    # 2️⃣ Total customers
    total_customers = Customer.objects.count()

    # 3️⃣ Total sales (number of invoices)
    total_sales = Invoice.objects.count()

    # 4️⃣ Gross sales & tax
    invoice_totals = Invoice.objects.aggregate(
        gross_sales=Sum("total_amount"),
        total_tax=Sum("tax_amount")
    )

    gross_sales = invoice_totals["gross_sales"] or 0
    total_tax = invoice_totals["total_tax"] or 0

    # 5️⃣ Total profit (net sales)
    total_profit = gross_sales - total_tax

    # 6️⃣ Monthly sales for graph
    monthly_sales = (
        Invoice.objects
        .annotate(month=TruncMonth("issued_date"))
        .values("month")
        .annotate(total=Sum("total_amount"))
        .order_by("month")
    )

    months = [m["month"].strftime("%b %Y") for m in monthly_sales]
    monthly_totals = [float(m["total"]) for m in monthly_sales]

    # 7️⃣ Low stock alerts
    low_stock_products = Product.objects.filter(stock__lte=5)

    # 8️⃣ Context
    context = {
        "total_products": total_products,
        "total_sales": total_sales,
        "total_customers": total_customers,
        "total_profit": round(total_profit, 2),
        "low_stock_products": low_stock_products,
        "months": months,
        "monthly_totals": monthly_totals,
    }

    return render(request, "core/owner/analysis.html", context)

#-----Category-----------

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'core/owner/category_list.html', {'categories': categories})


def category_add(request):
    if request.method == 'POST':
        form = ProdCategory(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Category Added..!")

            return redirect('cat_list')
    else:
        form= ProdCategory()
    return render(request, 'core/owner/category/add_category.html',{'form':form})


def category_edit(request, id):
    category = get_object_or_404(Category, pk=id)
    form = ProdCategory(request.POST or None, instance=category)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request,"Updated successfully")
            return redirect('cat_list')
    
    return render(request, 'core/owner/category/up_category.html', {'form': form})


def category_delete(request, id):
    category = get_object_or_404(Category, pk=id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted!')
    return render(request, 'core/owner/category/del_category.html', {'category': category})

# ===========Service=================

def service_list(request):
    services = Service.objects.all()
    return render(request, 'core/owner/service_list.html', {'services': services})


def service_add(request):
    
    # ✅ session check
    owner_id = request.session.get('shopowner_id')
    if not owner_id:
        return redirect('login')

    owner = ShopOwner.objects.get(sw_id=owner_id)

    if request.method == 'POST':
        form = ProdService(request.POST)

        if form.is_valid():

            service = form.save(commit=False)   # IMPORTANT
            service.shop_owner = owner          # attach owner
            service.save()

            messages.success(request, "Service Added..!")
            return redirect('ser_list')

    else:
        form = ProdService()

    return render(
        request,
        'core/owner/service/add_service.html',
        {'form': form}
    )


LOW_STOCK_LIMIT = 5


def check_low_stock(shop_owner):
    
    products = Product.objects.filter(shop_owner=shop_owner)

    with transaction.atomic():   # 🔥 prevents DB lock
        for product in products:

            available_qty = product.quantity

            if available_qty <= product.low_stock_limit:

                Notification.objects.update_or_create(
                    shop_owner=shop_owner,
                    notification_type="low_stock",
                    product_name=product.p_name,
                    defaults={
                        "message": f"Low stock alert: {product.p_name} only {available_qty} left"
                    }
                )

            else:
                Notification.objects.filter(
                    shop_owner=shop_owner,
                    notification_type="low_stock",
                    product_name=product.p_name
                ).delete()

def service_edit(request, id):
    service = get_object_or_404(Service, pk=id)

    if request.method == 'POST':
        form = ProdService(request.POST or None, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request,"Updated successfully..!")

            return redirect('ser_list')
    else:
        form = ProdService(instance=service)
    
    return render(request, 'core/owner/service/up_service.html', {'form': form})


def service_delete(request, id):
    service = get_object_or_404(Service, pk=id)
    if request.method == 'POST':
        service.delete()
        messages.success(request, 'Service deleted..!')
    
    return render(request, 'core/owner/service/del_service.html', {'service': service})


def update_service_status_final(request, pk):
    
    service = get_object_or_404(ServiceRequest, pk=pk)

    if request.method == "POST":

        new_status = request.POST.get("status")
        note = request.POST.get("note")

        service.status = new_status
        service.owner_note = note
        service.save()

        # -------------------------
        # POSTPONED MESSAGE
        # -------------------------
        if new_status == "POSTPONED":

            Notification.objects.create(
                shop_owner=service.shop_owner,
                notification_type="service",
                customer_name=service.customer.u_name,
                message="Your service is postponed. Retry soon."
            )

        # -------------------------
        # COMPLETED → CREATE INVOICE
        # -------------------------
        if new_status == "COMPLETED":
    
            if hasattr(service, "serviceinvoice"):
                messages.warning(request, "Invoice already generated")
                return redirect("service_requests")

            if not service.customer:
                messages.error(request, "Customer missing")
                return redirect("service_requests")

            amount = 0
            if service.service_type == "PAID" and service.service:
                amount = service.service.cost

            ServiceInvoice.objects.create(
                service_request=service,
                shop_owner=service.shop_owner,
                customer=service.customer,
                amount=amount,
                is_paid=(amount == 0)
            )


        messages.success(request, "Service status updated")

        return redirect("service_requests")

    return render(
        request,
        "core/owner/service/up_status.html",
        {"service": service}
    )


def generate_service_invoice(request, pk):

    service = get_object_or_404(ServiceRequest, pk=pk)

    # allow only completed services
    if service.status != "COMPLETED":
        messages.error(request, "Service not completed yet")
        return redirect("service_requests")

    # ✅ prevent duplicate invoice
    if hasattr(service, "serviceinvoice"):
        return redirect("print_service_invoice",
                        id=service.serviceinvoice.id)

    # -------------------------
    # CALCULATE AMOUNT
    # -------------------------
    service_charge = Decimal("0.00")

    if service.service_type == "PAID" and service.service:
        service_charge = Decimal(service.service.cost)

    tax = service_charge * Decimal("0.18")
    total = service_charge + tax

    # -------------------------
    # CREATE INVOICE
    # -------------------------
    invoice = ServiceInvoice.objects.create(
        service_request=service,
        shop_owner=service.shop_owner,
        customer=service.customer,
        service_charge=service_charge,
        tax_amount=tax,
        total_amount=total,
        is_paid=(total == 0),
    )

    messages.success(request, "Service Invoice Generated")

    return redirect("print_service_invoice", id=invoice.id)

def print_service_invoice(request, id):
    
    invoice = get_object_or_404(
    ServiceInvoice.objects.select_related(
        "customer",
        "shop_owner",
        "service_request",
        "service_request__service",
        "service_request__product_invoice__product"
    ),
    id=id
)


    return render(
        request,
        "core/owner/service/service_invoice.html",
        {
            "invoice": invoice,
            "service": invoice.service_request
        }
    )

def download_service_invoice(request, pk):

    invoice = get_object_or_404(ServiceInvoice, pk=pk)

    # ⭐ MARK AS CREATED
    invoice.invoice_created = True
    invoice.save()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'

    doc = SimpleDocTemplate(response)
    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            f"Customer: {invoice.customer.u_name}",
            styles['Normal']
        )
    )

    elements.append(
        Paragraph(
            f"Amount: ₹{invoice.amount}",
            styles['Normal']
        )
    )

    doc.build(elements)

    return response

def save_service_invoice(request, id):
    
    invoice = get_object_or_404(ServiceInvoice, id=id)

    # mark invoice as officially saved
    invoice.invoice_created = True
    invoice.save()

    messages.success(request, "Invoice saved to Manage Invoices")

    return redirect("invoice_list")


def owner_manage_invoices(request):
    
    owner = ShopOwner.objects.get(
        sw_id=request.session['shopowner_id']
    )

    filter_type = request.GET.get("type", "all")

    # PRODUCT INVOICES
    product_invoices = Invoice.objects.filter(
        items__product__shop_owner=owner
    ).distinct()

    # SERVICE INVOICES (ONLY CREATED)
    service_invoices = ServiceInvoice.objects.filter(
        shop_owner=owner,
        invoice_created=True
    ).select_related(
        "customer",
        "service_request__service"
    )

    if filter_type == "product":
        service_invoices = ServiceInvoice.objects.none()

    elif filter_type == "service":
        product_invoices = Invoice.objects.none()

    return render(request,
        "core/owner/invoice/invoice_list.html",
        {
            "product_invoices": product_invoices,
            "service_invoices": service_invoices,
            "filter_type": filter_type
        }
    )

def process_payment(request, id):
    
    invoice = get_object_or_404(ServiceInvoice, id=id)

    if request.method == "POST":

        method = request.POST.get("payment_method")

        invoice.payment_method = method
        invoice.is_paid = True
        invoice.save()

        # ⭐ UPDATE SERVICE STATUS FOR OWNER VIEW
        service = invoice.service_request
        service.status = "COMPLETED"
        service.save()

        messages.success(request, "Payment Successful ✅")

        return redirect("customer_invoices")


def sell_product(request):
    owner = ShopOwner.objects.get(sw_id=request.session['shopowner_id'])
    items = request.session.get('invoice_items', [])
    
    if request.method == "POST":
        form = SellProductForm(request.POST)
        if form.is_valid():
            request.session['customer_name'] = form.cleaned_data['customer_name']
            request.session['phone_no'] = form.cleaned_data['phone_no']
            request.session['payment_method'] = form.cleaned_data['payment_method']
            check_low_stock(owner)
    else:
        form = SellProductForm()

    products = Product.objects.all()

    return render(request, 'core/owner/sell_prod.html', {
        'form': form,
        'items': items,
        'products': products
    })


def print_bill(request):
    items = request.session.get("invoice_items", [])
    if not items:
        return redirect("sell_product")

    # ✅ READ FROM POST (NOT SESSION)
    c_name = (request.POST.get("customer_name") or "").strip()
    phone_no = (request.POST.get("phone_no") or "").strip()

    payment_method = request.POST.get("payment_method", "Cash")

    # ✅ CUSTOMER LOGIC
    # CUSTOMER LOGIC
    if c_name and phone_no:
        customer = Customer.objects.filter(phone_no=phone_no).first()

    if customer:
        customer.u_name = c_name
        customer.save()
    else:
        customer = Customer.objects.create(
            phone_no=phone_no,
            u_name=c_name
        )


    # ✅ CREATE INVOICE
    invoice = Invoice.objects.create(
        customer=customer,
        issued_date=timezone.now(),
        payment_method=payment_method
    )

    total = Decimal("0.00")

    for i in items:
        product = Product.objects.get(p_id=i["product_id"])
        quantity = int(i["quantity"])
        price = Decimal(i["price"])

        item_total = quantity * price

        InvoiceItem.objects.create(
            invoice=invoice,
            product=product,
            quantity=quantity,
            price=price,
            warranty=i["warranty"],
            total=item_total
        )

        total += item_total

    invoice.tax_amount = total * Decimal("0.18")
    invoice.total_amount = total + invoice.tax_amount
    invoice.save()

    # ✅ CLEAR CART
    request.session["invoice_items"] = []
    owner_id = request.session.get('shopowner_id')

    if owner_id:
        owner = ShopOwner.objects.get(sw_id=owner_id)
        check_low_stock(owner)

    return redirect("print_invoice", id=invoice.In_id)



def add_invoice_item(request):
    pid = request.GET.get('product_id')
    qty = int(request.GET.get('qty', 1))
    warranty = int(request.GET.get('warranty', 0))

    if qty < 1:
        return JsonResponse({'error': 'Invalid quantity'}, status=400)

    product = Product.objects.filter(p_id=pid).first()
    if not product:
        return JsonResponse({'error': 'Product not found'}, status=404)

    items = request.session.get('invoice_items', [])

    items.append({
        'product_id': product.p_id,
        'name': product.p_name,
        'quantity': qty,
        'price': float(product.price),
        'warranty': warranty,
        'total': float(product.price * qty)
    })

    request.session['invoice_items'] = items
    request.session.modified = True

    return JsonResponse({'items': items})

def print_invoice(request, id):
    invoice = Invoice.objects.get(In_id=id)

    return render(request, 'core/owner/Invoice/invoice_print.html', {
        'invoice': invoice
    })


from itertools import chain

def invoice_list(request):
    invoices = Invoice.objects.all()

    # Search by customer name
    search_query = request.GET.get('search', '')
    if search_query:
        invoices = invoices.filter(customer__u_name__icontains=search_query)

    # Sort by column
    sort_by = request.GET.get('sort', '')
    if sort_by in ['issued_date', '-issued_date', 'total_amount', '-total_amount', 'In_id', '-In_id']:
        invoices = invoices.order_by(sort_by)

    context = {
        'invoices': invoices,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'core/owner/Invoice/invoice_list.html', context)

def get_product_price(request):
    product_id = request.GET.get('product_id')

    try:
        product = Product.objects.get(p_id=product_id)  # ✅ FIX HERE
        return JsonResponse({'price': product.price})
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)


def get_customer_phone(request):
    cid = request.GET.get('customer_id')
    customer = Customer.objects.filter(c_id=cid).first()
    return JsonResponse({'phone': customer.phone_no if customer else ''})

def remove_invoice_item(request, index):
    items = request.session.get('invoice_items', [])
    if 0 <= index < len(items):
        items.pop(index)
        request.session['invoice_items'] = items
        request.session.modified = True
    return redirect('sell_product')

def invoice_preview(request, id):
    invoice = get_object_or_404(Invoice, In_id=id)

    return render(request, 'core/owner/Invoice/invoice_preview.html', {
        'invoice': invoice
    })

def delete_invoice(request, id):
    invoice = get_object_or_404(Invoice, In_id=id)
    invoice.delete()
    messages.success(request, "Invoice deleted successfully")
    return redirect('invoice_list')



def sales_reports(request):
    invoices = (
        Invoice.objects
        .annotate(day=TruncDate("issued_date"))
        .values("day")
        .annotate(
            total_invoices=Count("In_id"),
            gross_sales=Sum("total_amount"),
            tax=Sum("tax_amount"),
        )
        .order_by("-day")
    )

    report = []

    for inv in invoices:
        items = InvoiceItem.objects.filter(
            invoice__issued_date__date=inv["day"]
        ).aggregate(
            total_items=Sum("quantity"),
            profit=Sum("total")  # adjust if you store cost price
        )

        report.append({
            "date": inv["day"],
            "total_invoices": inv["total_invoices"],
            "total_items": items["total_items"] or 0,
            "gross_sales": inv["gross_sales"] or 0,
            "tax": inv["tax"] or 0,
            "net_sales": (inv["gross_sales"] or 0) - (inv["tax"] or 0),
            "profit": items["profit"] or 0,
        })

    return render(
        request,
        "core/owner/sales_report/sales_reports.html",
        {"report": report}
    )

def sales_day_detail(request, day):
    invoices = (
        Invoice.objects
        .filter(issued_date__date=day)
        .select_related("customer")
        .prefetch_related("items__product")
    )

    return render(
        request,
        "core/owner/sales_report/sales_details.html",
        {"invoices": invoices, "day": day},
    )

def product_stock(request):
    products = Product.objects.all()
    stock_data = []

    for p in products:
        sold_qty = (
            InvoiceItem.objects
            .filter(product=p)
            .aggregate(total=Sum("quantity"))["total"] or 0
        )

        available_qty = p.quantity - sold_qty
        stock_value = available_qty * p.price  # adjust field name if needed

        if available_qty <= 0:
            status = "Out of Stock"
        elif available_qty <= 1:
            status = "Low Stock"
        else:
            status = "In Stock"

        stock_data.append({
            "product": p,
            "quantity": available_qty,
            "sold_qty": sold_qty,
            "price": p.price,
            "stock_value": stock_value,
            "status": status,
        })

    return render(
    request,
    "core/owner/product_stock/stock.html",
    {
        "stock_data": stock_data,
    }
)
  
def notifications(request):
    if 'shopowner_id' not in request.session:
        return {}

    owner = ShopOwner.objects.get(sw_id=request.session['shopowner_id'])
    
    notifications = Notification.objects.filter(
        shop_owner=owner
    ).order_by('-created_at')

    return {
        'notifications': notifications,
        'notification_count': notifications.filter(is_read=False).count()
    }
    
    
def notifications_context(request):
    if hasattr(request, "shop_owner"):
        notifications = Notification.objects.filter(is_read=False)
        return {
            "notifications": notifications,
            "notification_count": notifications.count()
        }
    return {}


def service_reminder():
    tomorrow = timezone.now().date() + timedelta(days=1)

    services = ServiceRequest.objects.filter(
        scheduled_date=tomorrow,
        status='ACCEPTED'
    )

    for s in services:
        Notification.objects.create(
            shop_owner=s.product_invoice.customer.shop_owner,
            message=f"Service reminder for {s.product_invoice.product.name} tomorrow at {s.scheduled_time}"
        )
        

# def accept_service(request, pk):
    
#     sr = get_object_or_404(ServiceRequest, pk=pk)

#     if request.method == "POST":

#         sr.scheduled_date = request.POST['date']
#         sr.scheduled_time = request.POST['time']
#         sr.status = "ACCEPTED"
#         sr.save()

#         # Notification for customer
#         Notification.objects.create(
#             shop_owner=sr.shop_owner,
#             notification_type="info",
#             message=f"Service scheduled on {sr.scheduled_date}"
#         )

#         messages.success(request, "Service accepted")


#         send_whatsapp(
#         sr.customer.phone_no,
#         f"Service scheduled on {sr.scheduled_date}"
#         )        
#         print("Send WhatsApp to:", sr.customer.phone_no)

#         return redirect('service_requests')

#     return render(request,'core/owner/service/accept_service.html',{'sr':sr})

def accept_service(request, pk):
    sr = get_object_or_404(ServiceRequest, pk=pk)

    if request.method == "POST":
        date = request.POST['date']
        time = request.POST['time']
        ampm = request.POST['ampm']

        # Convert time to 24-hour format
        hour, minute = map(int, time.split(":"))
        if ampm.upper() == "PM" and hour < 12:
            hour += 12
        elif ampm.upper() == "AM" and hour == 12:
            hour = 0

        sr.scheduled_date = date
        sr.scheduled_time = f"{hour:02d}:{minute:02d}"
        sr.status = "ACCEPTED"
        sr.save()

        # Notification
        Notification.objects.create(
            shop_owner=sr.shop_owner,
            notification_type="info",
            message=f"Service scheduled on {sr.scheduled_date} at {sr.scheduled_time}"
        )

        messages.success(request, "Service accepted ✅")

        send_whatsapp(
            sr.customer.phone_no,
            f"Service scheduled on {sr.scheduled_date} at {sr.scheduled_time}"
        )
        print("Send WhatsApp to:", sr.customer.phone_no)

        return redirect('service_requests')

    return render(request, 'core/owner/service/accept_service.html', {'sr': sr})

# def complete_service(request, pk):
    
#     sr = get_object_or_404(ServiceRequest, pk=pk)

#     sr.status = "COMPLETED"
#     sr.save()

#     ServiceInvoice.objects.create(
#         service_request=sr,
#         amount=sr.service.cost,
#         is_paid=False
#     )

#     Notification.objects.create(
#         shop_owner=sr.shop_owner,
#         notification_type="service",
#         message="Service completed & invoice generated"
#     )

#     messages.success(request, "Service completed")

#     return redirect("service_requests")


def service_reminder():
    
    tomorrow = timezone.now().date() + timedelta(days=1)

    services = ServiceRequest.objects.filter(
        scheduled_date=tomorrow,
        status="ACCEPTED"
    )

    for s in services:
        Notification.objects.create(
            shop_owner=s.product_invoice.customer.shop_owner,
            message=f"Reminder: Service tomorrow at {s.scheduled_time}"
        )

# def complete_service(request, pk):

#     service = ServiceRequest.objects.get(pk=pk)
#     service.status = "COMPLETED"
#     service.save()

#     amount = 0

#     if service.service_type == "PAID":
#         amount = service.service.cost

#     ServiceInvoice.objects.create(
#         service_request=service,
#         amount=amount,
#         is_paid=(amount == 0)
#     )

#     Notification.objects.create(
#         shop_owner=request.shop_owner,
#         message="Service completed & invoice generated"
#     )

#     return redirect('service_invoices')
def service_requests(request):
    owner_session_id = request.session.get('shopowner_id')

    if not owner_session_id:
        return redirect('login')

    owner = ShopOwner.objects.filter(sw_id=owner_session_id).first()

    requests = ServiceRequest.objects.filter(shop_owner=owner)

    # 🔹 FILTERS
    status = request.GET.get('status')
    service_type = request.GET.get('type')
    search = request.GET.get('search')

    if status:
        requests = requests.filter(status=status)

    if service_type:
        requests = requests.filter(service_type=service_type)

    if search:
        requests = requests.filter(customer__u_name__icontains=search)


    requests = requests.select_related(
        'customer',
        'service',
        'product_invoice__product'
    ).order_by('-id')

    return render(request, 'core/owner/service/service_req.html', {
        'requests': requests
    })


def send_whatsapp(phone, msg):
    print(f"WhatsApp sent to {phone}: {msg}")



def service_calendar(request):
    
    owner = ShopOwner.objects.get(
        sw_id=request.session['shopowner_id']
    )

    services = ServiceRequest.objects.filter(
        shop_owner=owner,
        status="ACCEPTED"
    )

    events = []

    for s in services:
        events.append({
            "title": s.customer.u_name,
            "date": str(s.scheduled_date)
        })

    return JsonResponse(events, safe=False)


from django.views.decorators.http import require_POST

@require_POST
def delete_multiple_requests(request):
    ids = request.POST.getlist('selected_requests')

    ServiceRequest.objects.filter(id__in=ids).delete()

    messages.success(request, "Selected requests deleted 🗑️")

    return redirect('service_requests')

# ================Customer View==========================
def customer_dashboard(request): 
    if 'customer_id' not in request.session: 
        return redirect('login') 
    
    cid = request.session['customer_id'] 
    invoices = Invoice.objects.filter(customer_id=cid) 
    items = InvoiceItem.objects.filter(invoice__customer_id=cid) 
    services = ServiceRequest.objects.filter(customer_id=cid) 
    context = { "total_products": items.count(), 
               "total_invoices": invoices.count(), 
               "pending_services": services.filter(status="PENDING").count(), 
               "completed_services": services.filter(status="COMPLETED").count(), } 
    return render(request, "core/customer/c_dashboard.html", context)


def customer_products(request):
    
    if 'customer_id' not in request.session:
        return redirect('login')

    purchases = InvoiceItem.objects.filter(
        invoice__customer_id=request.session['customer_id']
    ).select_related('product', 'invoice')

    return render(
        request,
        "core/customer/c_prod.html",
        {"purchases": purchases}
    )
        
def request_service(request, item_id):
    
    if 'customer_id' not in request.session:
        return redirect('login')

    customer = get_object_or_404(
        Customer,
        pk=request.session['customer_id']
    )

    item = None

    # product-based service
    if item_id != 0:
        item = get_object_or_404(
            InvoiceItem,
            id=item_id,
            invoice__customer=customer
        )

    form = ServiceRequestForm(request.POST or None)

    if request.method == "POST" and form.is_valid():

        service_request = form.save(commit=False)

        service_request.customer = customer
        service_request.product_invoice = item
        service_request.service_type = "PAID"
        service_request.problem = form.cleaned_data['problem']

        # ✅ OWNER ASSIGNMENT (CRITICAL)
        if item:
            service_request.shop_owner = item.invoice.shop_owner
        else:
            service_request.shop_owner = service_request.service.shop_owner

        service_request.save()

        messages.success(request, "Service request sent")
        return redirect("manage_services")

    return render(request,
        "core/customer/req_service.html",
        {"form": form, "item": item}
    )

  
def manage_services(request):
    if 'customer_id' not in request.session:
        return redirect('login')

    customer_id = request.session['customer_id']

    # service requests
    services = ServiceRequest.objects.filter(
        customer_id=customer_id
    ).select_related('product_invoice__product')

    # purchased products (THIS WAS MISSING)
    purchases = InvoiceItem.objects.filter(
        invoice__customer_id=customer_id
    ).select_related('product_invoice__product')

    return render(request, 'core/customer/manage_service.html', {
        'services': services,
        'purchases': purchases,   # ✅ IMPORTANT
    })

def cancel_service(request, pk):
    
    if 'customer_id' not in request.session:
        return redirect('login')

    customer_id = request.session['customer_id']

    service = get_object_or_404(
        ServiceRequest,
        pk=pk,
        customer_id=customer_id
    )

    # allow cancel only if not completed
    if service.status == "PENDING":
        service.delete()
        messages.success(request, "Service request cancelled")

    return redirect("manage_services")


def customer_invoices(request):
    
    invoices = ServiceInvoice.objects.filter(
        service_request__customer=request.user
    )

    return render(request,
        "core/customer/invoice_detail.html",
        {"invoices": invoices})




# ===============================
# SINGLE INVOICE DETAIL
# ===============================
def invoice_detail(request, invoice_id):
    
    invoice = get_object_or_404(
        Invoice,
        In_id=invoice_id,
        customer_id=request.session['customer_id']
    )

    return render(
        request,
        "core/customer/invoice_detail.html",
        {"invoice": invoice}
    )

def customer_service_invoices(request):
    
    customer_id = request.session.get("customer_id")

    invoices = ServiceInvoice.objects.filter(
        customer_id=customer_id
    ).select_related(
        "service_request",
        "service_request__service",
        "shop_owner"
    ).order_by("-invoice_date")

    return render(
        request,
        "core/customer/invoice_manage.html",
        {"invoices": invoices}
    )


from django.http import JsonResponse

def notification_api(request):

    if 'shopowner_id' not in request.session:
        return JsonResponse({"count": 0})

    owner = ShopOwner.objects.get(
        sw_id=request.session['shopowner_id']
    )

    notifications = Notification.objects.filter(
        shop_owner=owner,
        is_read=False
    )

    data = {
        "count": notifications.count(),
        "messages": list(
            notifications.values("message", "created_at")
        )
    }

    return JsonResponse(data)



def download_service_invoice_pdf(request, pk):
    
    #  use pk (maps to In_id automatically)
    invoice = get_object_or_404(ServiceInvoice, pk=pk)

    # render HTML
    html_string = render_to_string(
        "core/customer/invoice_pdf.html",
        {"invoice": invoice}
    )

    # create PDF
    html = HTML(
        string=html_string,
        base_url=request.build_absolute_uri('/')  # IMPORTANT
    )
    pdf = html.write_pdf()

    # download response
    response = HttpResponse(pdf, content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice.pk}.pdf"'

    return response
# def service_calendar_page(request):
    
#     if 'shopowner_id' not in request.session:
#         return redirect('login')

#     return render(
#         request,
#         "core/owner/service_calendar.html"
#     )


def service_calendar(request):

    owner = ShopOwner.objects.get(
        sw_id=request.session['shopowner_id']
    )

    services = ServiceRequest.objects.filter(
        shop_owner=owner,
        status="ACCEPTED"
    )

    events = []

    for s in services:
        events.append({
            "title": f"{s.customer.u_name} - {s.product_invoice.product.p_name}",
            "start": str(s.scheduled_date),
        })

    return JsonResponse(events, safe=False)

def pay_service_invoice(request, id):
    
    invoice = get_object_or_404(
        ServiceInvoice,
        id=id
    )

    if request.method == "POST":

        method = request.POST.get("payment_method")

        invoice.payment_method = method
        invoice.is_paid = True
        invoice.save()

        messages.success(request, "Payment Successful")

        return redirect("customer_service_invoices")

    return render(
        request,
        "core/customer/pay_invoice.html",
        {"invoice": invoice}
    )

def upi_payment_page(request, id):
    
    invoice = get_object_or_404(ServiceInvoice, id=id)

    # simulate payment success
    invoice.is_paid = True
    invoice.payment_status = "SUCCESS"
    invoice.save()

    messages.success(request, "UPI Payment Successful")

    return redirect("customer_service_invoices")    

@csrf_exempt
def payment_success(request):

    if request.method == "POST":

        payment_id = request.POST.get("razorpay_payment_id")
        order_id = request.POST.get("razorpay_order_id")
        signature = request.POST.get("razorpay_signature")

        invoice = ServiceInvoice.objects.get(
            razorpay_order_id=order_id
        )

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        params = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        try:
            client.utility.verify_payment_signature(params)

            invoice.razorpay_payment_id = payment_id
            invoice.razorpay_signature = signature
            invoice.payment_method = "RAZORPAY"
            invoice.payment_status = "SUCCESS"
            invoice.is_paid = True
            invoice.save()

            messages.success(request, "Payment Successful ✅")

        except Exception as e:
            print("Verification Error:", e)
            messages.error(request, "Payment verification failed")

    return redirect("customer_service_invoices")


def payment_options(request, id):

    invoice = get_object_or_404(ServiceInvoice, id=id)

    if invoice.is_paid:
        messages.info(request, "Already Paid")
        return redirect("customer_service_invoices")

    return render(
        request,
        "core/customer/pay_invoice.html",
        {"invoice": invoice}
    )
    
def process_payment(request, id):
    
    invoice = get_object_or_404(ServiceInvoice, id=id)

    if request.method == "POST":

        method = request.POST.get("payment_method")
        upi_id = request.POST.get("upi_id")

        invoice.payment_method = method

        if method == "UPI":
            invoice.upi_id = upi_id

        invoice.is_paid = True
        invoice.payment_date = timezone.now()
        invoice.save()

        messages.success(request, "Payment Successful ✅")

    return redirect("customer_service_invoices")
    

def create_razorpay_order(request, id):

    invoice = get_object_or_404(ServiceInvoice, id=id)

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    amount = int(float(invoice.amount) * 100)

    order = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })

    # save order id in DB
    invoice.razorpay_order_id = order['id']
    invoice.save()

    return render(request, "core/customer/razerpay_pay.html", {
        "invoice": invoice,
        "order_id": order['id'],
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "amount": amount
    })