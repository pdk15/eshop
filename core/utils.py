from twilio.rest import Client
from datetime import timedelta
from django.utils import timezone

def send_whatsapp(phone, message):

    account_sid = "YOUR_SID"
    auth_token = "YOUR_TOKEN"

    client = Client(account_sid, auth_token)

    client.messages.create(
        body=message,
        from_='whatsapp:+14155238886',
        to=f'whatsapp:+91{phone}'
    )



def is_under_warranty(item):

    warranty_days = item.warranty * 30
    expiry = item.purchase_date + timedelta(days=warranty_days)

    return timezone.now().date() <= expiry
