import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from tax_service.views import OrderViewSet
from rest_framework.test import APIRequestFactory

factory = APIRequestFactory()
request = factory.get('/api/orders/', {'ordering': 'id'})
view = OrderViewSet.as_view({'get': 'list'})
response = view(request)
data = response.data.get('results', [])
print("id ASC:", [x['id'] for x in data[:2]])

request2 = factory.get('/api/orders/', {'ordering': '-id'})
response2 = view(request2)
data2 = response2.data.get('results', [])
print("-id DESC:", [x['id'] for x in data2[:2]])
