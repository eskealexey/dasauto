from django.urls import path
from . import views


urlpatterns = [
    path('clients/', views.dashboard, name='dashboard'),
    path('clients/list/', views.client_list, name='client_list'),
    path('clients/create/', views.client_create, name='client_create'),
    path('clients/<int:pk>/', views.client_detail, name='client_detail'),
    path('clients/<int:pk>/edit/', views.client_edit, name='client_edit'),
    path('api/clients/<int:client_id>/cars/', views.get_client_cars, name='client_cars_api'),
]