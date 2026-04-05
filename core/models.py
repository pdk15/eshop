from django.db import models  #imports Django’s ORM (Object Relational Mapping) models.
from django.contrib.auth.models import User   #Django comes with a built-in authentication system.
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.contrib.auth.hashers import make_password , check_password 
from django.core.validators import MinValueValidator
from django.utils.timezone import now

    
class ShopOwner(models.Model):
    sw_id = models.AutoField(primary_key=True)
    sw_uname = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    phone_no = models.CharField(max_length=15)  # IntegerField not ideal for phone numbers
    address = models.CharField(max_length=150)

    reset_token = models.CharField(max_length=100, blank=True, null=True)
    def __str__(self):
        return self.sw_uname
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

class Customer(models.Model):
    c_id = models.AutoField(primary_key=True)
    u_name = models.CharField(max_length=20)
    password = models.CharField(max_length=128)
    email = models.EmailField(max_length=100)
    address = models.CharField(max_length=150)
    phone_no = models.CharField(max_length=15)
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def __str__(self):
        return self.u_name
    
class ShopInfo(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    instagram = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    whatsapp = models.CharField(max_length=15, blank=True, null=True)

class Category(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    ct_id = models.AutoField(primary_key=True)
    ct_name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')
    
    def __str__(self):
        return self.ct_name  # corrected capitalization


class Product(models.Model):
    shop_owner = models.ForeignKey(
        ShopOwner,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    p_id = models.AutoField(primary_key=True)
    p_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Tax amount for the product")
    warranty = models.IntegerField(help_text="Warranty in months")
    description = models.TextField(blank=True, null=True, help_text="More Product details")
    quantity = models.PositiveIntegerField(default=1)

    stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of units in stock. Must be zero or positive."
    )

    
    def __str__(self):
        return f"{self.p_name} ({self.category.ct_name})"

class Service(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    SERVICE_TYPE = [
        ('INSTALL', 'Installation'),
        ('PERIODIC', 'Periodic'),
        ('WARRANTY', 'Warranty'),
        ('PAID', 'Paid'),
    ]
    s_id = models.AutoField(primary_key=True)
    s_name = models.CharField(max_length=100)
    shop_owner = models.ForeignKey(ShopOwner, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True, help_text="More details")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='services')
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')
    
    def __str__(self):
        return f"{self.s_name} ({self.category})"


class SupplyService(models.Model):
    ss_id = models.AutoField(primary_key=True)
    ss_name = models.CharField(max_length=100)
    ss_date = models.DateTimeField(auto_now_add=True)
    ss_cost = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50)
    
    def __str__(self):
        return f"{self.ss_name}"


class ShopPurProd(models.Model):
    sp_id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    issued_date = models.DateTimeField(default=timezone.now)
    payment_method = models.CharField(max_length=20, choices=[('CASH','Cash'),('CARD','Card'),('UPI','UPI'),('ONLINE','Online')], default='CASH')
    sp_date = models.DateTimeField(auto_now_add=True)
    quantity = models.PositiveIntegerField(default=1)
    replacement = models.CharField(max_length=10, choices=[('Yes','Yes'),('No','No')], default='No')

    def __str__(self):
        return f"{self.sp_id} - {self.product.p_name}"


class Invoice(models.Model):
    In_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    issued_date = models.DateTimeField(default=timezone.now)
    payment_method = models.CharField(max_length=20)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Invoice {self.In_id} - {self.customer.u_name}"

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    warranty = models.IntegerField(default=0)   # months
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # ✅ WARRANTY CHECK
    def warranty_valid(self):
        purchase_date = self.invoice.issued_date.date()

        expiry_date = purchase_date + relativedelta(
            months=self.warranty
        )

        return timezone.now().date() <= expiry_date

    # ✅ OPTIONAL (very useful)
    def warranty_expiry(self):
        return self.invoice.issued_date.date() + relativedelta(
            months=self.warranty
        )


class Notification(models.Model):
    TYPE_CHOICES = (
        ('low_stock', 'Low Stock'),
        ('service', 'Service Request'),
        ('info', 'Info'),
    )
    product = models.ForeignKey(
    Product,
    on_delete=models.CASCADE,
    null=True,
    blank=True
)


    shop_owner = models.ForeignKey(ShopOwner, on_delete=models.CASCADE)

    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)


    purchase_date = models.DateField(auto_now_add=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    available_qty = models.IntegerField(blank=True, null=True)

    customer_name = models.CharField(max_length=100, blank=True, null=True)
    message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

class ServiceRequest(models.Model):
    
    STATUS_CHOICES = [ 
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('COMPLETED', 'Completed'),
        ('POSTPONED', 'Postponed'),
    ]
    problem = models.TextField(null=True, blank=True)   # ✅ must exist

    SERVICE_TYPE = [
        ('FREE', 'Free'),
        ('PAID', 'Paid'),
        ('WARRANTY', 'Warranty'),
    ]

    product_invoice = models.ForeignKey( InvoiceItem, on_delete=models.SET_NULL, null=True,blank=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    shop_owner = models.ForeignKey(ShopOwner,on_delete=models.CASCADE, null=True, blank=True)

    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE)

    scheduled_date = models.DateField(null=True, blank=True)
    scheduled_time = models.TimeField(null=True, blank=True)

    status = models.CharField(max_length=20,
                              choices=STATUS_CHOICES,
                              default='PENDING')

    created_at = models.DateTimeField(auto_now_add=True)


class ServiceInvoice(models.Model):

    PAYMENT_METHODS = [
            ('CASH', 'Cash'),
            ('UPI', 'UPI'),
            ('RAZORPAY', 'Razorpay'),            
        ]
    service_request = models.OneToOneField(ServiceRequest, on_delete=models.CASCADE )
    shop_owner = models.ForeignKey(ShopOwner,on_delete=models.CASCADE,null=True,blank=True )
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE,null=True,blank=True )
    pdf_file = models.FileField(upload_to="service_invoices/",null=True,blank=True)


    invoice_date = models.DateField(auto_now_add=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2 )
    payment_status = models.CharField( max_length=20,default="PENDING" )
    is_paid = models.BooleanField(default=False)

    # ✅ NEW FIELDS
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, null=True, blank=True   )

    upi_id = models.CharField(max_length=100, null=True, blank=True)

    transaction_id = models.CharField(max_length=100, blank=True, null=True )

    razorpay_order_id = models.CharField(max_length=200, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=200, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Service Invoice #{self.id}"
