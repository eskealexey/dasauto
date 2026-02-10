# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Добавляем поле в список
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone', 'is_staff')

    # Добавляем в поля для редактирования
    fieldsets = UserAdmin.fieldsets + (
        ('Контактная информация', {
            'fields': ('phone',),
        }),
    )

    # Добавляем в поля для создания
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Контактная информация', {
            'fields': ('phone',),
        }),
    )