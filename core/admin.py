from django.contrib import admin
from .models import ShopOwner ,ShopInfo, Customer , Category ,Product , ShopPurProd ,Service , SupplyService , Invoice
admin.site.register(ShopOwner)
admin.site.register(Customer)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ShopPurProd)
admin.site.register(Service )
admin.site.register(SupplyService)
admin.site.register(Invoice )
admin.site.register(ShopInfo)

# Register your models here.
