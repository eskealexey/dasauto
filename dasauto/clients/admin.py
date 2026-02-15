from django.contrib import admin
from django.db.models import Count, Sum, Value, DecimalField, IntegerField
from django.db.models.functions import Coalesce

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'email', 'client_type', 'created_by', 'get_orders_count', 'get_total_spent',
                    'is_active']
    list_filter = ['client_type', 'source', 'is_active', 'created_at']
    search_fields = ['first_name', 'last_name', 'phone', 'email', 'company_name', 'inn']
    readonly_fields = ['created_at', 'updated_at', 'get_total_spent', 'get_orders_count']

    fieldsets = (
        ('Основная информация', {
            'fields': ('created_by', 'client_type', 'first_name', 'last_name', 'patronymic')
        }),
        ('Контакты', {
            'fields': ('phone', 'email', 'additional_phone')
        }),
        ('Юридическое лицо', {
            'fields': ('company_name', 'inn', 'kpp'),
            'classes': ('collapse',)
        }),
        ('Дополнительно', {
            'fields': ('address', 'discount', 'source', 'tags', 'notes')
        }),
        ('Статистика', {
            'fields': ('get_total_spent', 'get_orders_count', 'is_active', 'created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            orders_count_annotated=Coalesce(
                Count('orders', distinct=True),
                Value(0),
                output_field=IntegerField()
            ),
            total_spent_annotated=Coalesce(
                Sum('orders__total_amount'),
                Value(0),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )

    def get_orders_count(self, obj):
        return obj.orders_count_annotated if hasattr(obj, 'orders_count_annotated') else obj.orders.count()

    get_orders_count.short_description = 'Кол-во заказов'
    get_orders_count.admin_order_field = 'orders_count_annotated'

    def get_total_spent(self, obj):
        amount = obj.total_spent_annotated if hasattr(obj, 'total_spent_annotated') else \
        obj.orders.aggregate(total=Sum('total_amount'))['total'] or 0
        return f"{amount} ₽"

    get_total_spent.short_description = 'Всего потрачено'
    get_total_spent.admin_order_field = 'total_spent_annotated'