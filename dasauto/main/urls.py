from django.urls import path
from .views import index

urlpatterns = [
    path('', index, name='home'),
    # path('<int:sort_id>/', sort_detail, name='sort_id'),
    # path('dop/<int:info_id>/', info_detail, name='info_detail'),
    # path('found/', found, name='found'),
]