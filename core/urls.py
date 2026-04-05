from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.shop_login, name='login'),
    path('dashboard/', views.shop_dashboard, name='dashboard'),
    path('logout/', views.shopowner_logout, name='logout'),
    path('', views.home, name='home'),
    path('services/', views.services, name='services'),
    path('about/', views.about, name='about'),
    path('book-service/',views.bookservice,name='book_service'),
    path('dash', views.analysis, name='shop_analysis'),
    path('products/manage', views.manage_products, name='manage_prod'),
    path('products/add/', views.productAdd, name='product_add'),
    path('products/edit/<int:pk>/', views.update_product , name='product_update'),
    path('products/delete/<int:pk>/', views.delete_prod, name='delete_con'),
    path('categories', views.category_list, name='cat_list'),
    path('categories/add', views.category_add, name='add_category'),
    path('categories/edit/<int:id>/', views.category_edit, name='update_cat'),
    path('categories/delete/<int:id>/', views.category_delete, name='delete_cat'),
    
    path('services', views.service_list, name='ser_list'),
    path('services/add', views.service_add, name='ser_add'),
    path('services/edit/<int:id>/', views.service_edit, name='ser_update'),
    path('services/delete/<int:id>/', views.service_delete, name='ser_delete'),
    
    path('register/<str:role>/', views.role_reg, name='role_reg'),
    
    path('shopowner/profile/', views.shopowner_profile, name='ow_detail'),
    
    path('sell-product/', views.sell_product, name='sell_product'),
    path('add-invoice-item/', views.add_invoice_item, name='add_invoice_item'),

    path('invoice/print/<int:id>/', views.print_invoice, name='print_invoice'),
    path('api/product-price/', views.get_product_price, name='product_price'),
    path('remove-invoice-item/<int:index>/', views.remove_invoice_item, name='remove_invoice_item'),
    path('invoice/view/<int:id>/', views.invoice_preview, name='invoice_preview'),

    path('invoice/print/', views.print_bill, name='print_bill'),
    path('invoice/delete/<int:id>/', views.delete_invoice, name='delete_invoice'),
    path('invoice/list/', views.invoice_list, name='invoice_list'),


    path('sales_report/', views.sales_reports, name='sales_report'),

    path("sales-report/<str:day>/", views.sales_day_detail, name="sales_day_detail"),
    path('Product_stock/', views.product_stock, name='product_stock'),


    path('shop/forgot-password/', views.forgot_password, name='forget_password'),

    # RESET PASSWORD (link containing token)
    path('shop/reset-password/<uuid:token>/', views.reset_password, name='reset_password'),
    path('service/requests/', views.service_requests, name='service_requests'),
    path('service/accept/<int:pk>/',views.accept_service,name='accept_service'),
    path( 'service/update/<int:pk>/', views.update_service_status_final,name='update_status'),

    path("service/invoice/<int:pk>/",views.generate_service_invoice, name="generate_service_invoice"),
    path( "save-service-invoice/<int:id>/", views.save_service_invoice, name="save_service_invoice"),
path('delete-multiple/', views.delete_multiple_requests, name='delete_multiple_requests'),


path(   
    "service/invoice/print/<int:id>/",
    views.print_service_invoice,
    name="print_service_invoice"
),



    path(
        'customer/',
        views.customer_dashboard,
        name='customer_dashboard'
    ),

    # =========================
    # PRODUCTS (Purchased)
    # =========================
    path(
        'customer/products/',
        views.customer_products,
        name='customer_product'
    ),

    # =========================
    # SERVICE MANAGEMENT
    # =========================
    path(
        'customer/services/',
        views.manage_services,
        name='manage_services'
    ),

    path(
        "request-service/<int:item_id>/",
        views.request_service,
        name="request_service"
    ),
path(
    'customer/service/cancel/<int:pk>/',
    views.cancel_service,
    name='cancel_service'
),

    # =========================
    # INVOICES
    # =========================
    path(
    "customer/service-invoices/",
    views.customer_service_invoices,
    name="customer_service_invoices"
),


    path(
        'customer/invoices/<int:invoice_id>/',
        views.invoice_detail,
        name='invoice_detail'
    ),
    path(
    "pay-invoice/<int:id>/",
    views.pay_service_invoice,
    name="pay_service_invoice"
),

    
#     path(
#     "owner/service-calendar/",
#     views.service_calendar_page,
#     name="service_calendar_page"
# ),

path(
    "service-calendar/",
    views.service_calendar,
    name="service_calendar"
),

path(
    "service-invoice/pdf/<int:pk>/",
    views.download_service_invoice_pdf,
    name="download_service_invoice_pdf",
),




path("pay-invoice/<int:id>/", views.pay_service_invoice,name="pay_service_invoice"),

path("upi-payment/<int:id>/",views.upi_payment_page,name="upi_payment_page"),
path("payment/<int:id>/",views.payment_options, name="payment_options"),
path("process-payment/<int:id>/",views.process_payment,name="process_payment"),
path('create-razorpay-order/<int:id>/', views.create_razorpay_order, name='create_razorpay_order'),

    # Razorpay success callback
    path('payment-success/', views.payment_success, name='payment_success'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
