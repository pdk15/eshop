from django import forms
from .models import Product , Category , Service , ShopOwner , ShopPurProd , Invoice  , Customer ,ServiceRequest

class ProductForm(forms.ModelForm):
    
    class Meta:
        model = Product
        fields =["category","p_id","p_name","price","tax_amount","quantity","warranty","description"]
        labels = {
            'category': 'Category Name',
            'p_name': 'Product Name ',
            'price': 'Price ',
            'tax_amount': 'Tax Amount',
            'quantity' : 'Quantity',
            'warranty': 'Product Warranty',
            'description': 'Description',
        }
 
class ProdCategory(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['ct_name', 'status']  # Only editable fields
        labels = {
            'ct_name': 'Category Name',
            'status': 'Status ',
        }
        widgets = {
            'ct_name': forms.TextInput(attrs={
                'class': 'form-control',    
                'placeholder': 'Enter Category Name'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        
class ProdService(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['s_name', 'category', 'cost', 'status', 'description']
        labels = {
            's_name': 'Service Name',
            'category': 'Category Name',
            'cost': 'Service Cost',
            'status': 'Status',
        }
        widgets = {
            's_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Service Name'
            }),

            'category': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select Category'
            }),

            'cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Service Cost'
            }),

            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }


class ShopOwnerProfile(forms.ModelForm):
    class Meta:
        model = ShopOwner
        fields = ['sw_uname', 'email', 'phone_no', 'address']
        labels = {
            'sw_uname': 'Username',
            'email': 'Email',
            'phone_no': 'Phone Number',
            'address': 'Address',
        }
        widgets = {
            'sw_uname': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_no': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }



class SellProductForm(forms.Form):
    customer_name = forms.CharField(
        widget=forms.TextInput(attrs={'class':'form-control'})
    )
    phone_no = forms.CharField(
        widget=forms.TextInput(attrs={'class':'form-control' })
    )
    payment_method = forms.ChoiceField(
        choices=[
            ('CASH','Cash'),
            ('CARD','Card'),
            ('UPI','UPI'),
            ('ONLINE','Online')
        ],
        widget=forms.Select(attrs={'class':'form-control'})
    )
    
class ServiceRequestForm(forms.ModelForm):
    problem = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Describe the issue..."}),
        required=True
    )

    class Meta:
        model = ServiceRequest
        fields = ["service", "problem"]

        widgets = {
            "service": forms.Select(attrs={"class": "form-control"})
        }

    def __init__(self, *args, **kwargs):
        # We pop the shop_owner so it doesn't interfere with standard form init
        shop_owner = kwargs.pop('shop_owner', None)
        super(ServiceRequestForm, self).__init__(*args, **kwargs)
        
        # If an owner is identified, only show THEIR services
        if shop_owner:
            self.fields['service'].queryset = Service.objects.filter(shop_owner=shop_owner, status='Active')
