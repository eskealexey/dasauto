from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()
from django.core.validators import MinValueValidator, MaxValueValidator


class Client(models.Model):
    """Модель клиента автомастерской"""

    CLIENT_TYPE_CHOICES = [
        ('individual', 'Физическое лицо'),
        ('legal', 'Юридическое лицо'),
        ('regular', 'Постоянный клиент'),
    ]

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Добавлено",
        related_name="clients"  # Теперь user.clients.all() — список клиентов, добавленных этим пользователем
    )
    client_type = models.CharField(max_length=20, choices=CLIENT_TYPE_CHOICES, default='individual')

    # Основная информация
    first_name = models.CharField('Имя', max_length=100)
    last_name = models.CharField('Фамилия', max_length=100)
    patronymic = models.CharField('Отчество', max_length=100, blank=True)

    # Контактные данные
    phone = models.CharField('Телефон', max_length=20, unique=True, db_index=True)
    email = models.EmailField('Email', blank=True)
    additional_phone = models.CharField('Доп. телефон', max_length=20, blank=True)

    # Для юрлиц
    company_name = models.CharField('Название компании', max_length=200, blank=True)
    inn = models.CharField('ИНН', max_length=12, blank=True, unique=True, null=True)
    kpp = models.CharField('КПП', max_length=9, blank=True)

    # Адрес
    address = models.TextField('Адрес', blank=True)

    # Дополнительная информация
    discount = models.DecimalField(
        'Скидка %',
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    notes = models.TextField('Заметки', blank=True)

    # Метки и источники
    source = models.CharField('Источник', max_length=100, blank=True)
    tags = models.CharField('Теги', max_length=200, blank=True, help_text='Через запятую')

    # Системные поля
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.patronymic}".strip()

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name} {self.patronymic}".strip()

    @property
    def total_spent(self):
        """Общая сумма потраченная клиентом"""
        total = self.orders.aggregate(total=models.Sum('total_amount'))['total']
        return total or 0

    # Удаляем property orders_count - будем использовать аннотацию в запросах


class Car(models.Model):
    """Модель автомобиля клиента"""

    TRANSMISSION_CHOICES = [
        ('manual', 'Механика'),
        ('automatic', 'Автомат'),
        ('robot', 'Робот'),
        ('variator', 'Вариатор'),
    ]

    FUEL_CHOICES = [
        ('petrol', 'Бензин'),
        ('diesel', 'Дизель'),
        ('gas', 'Газ'),
        ('electric', 'Электричество'),
        ('hybrid', 'Гибрид'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='cars')

    # Информация об авто
    brand = models.CharField('Марка', max_length=100, db_index=True)
    model = models.CharField('Модель', max_length=100, db_index=True)
    year = models.PositiveIntegerField('Год выпуска', null=True, blank=True)
    vin = models.CharField('VIN', max_length=17, unique=True, blank=True, null=True)
    license_plate = models.CharField('Госномер', max_length=10, blank=True, db_index=True)

    # Технические характеристики
    engine_volume = models.DecimalField('Объем двигателя', max_digits=3, decimal_places=1, null=True, blank=True)
    engine_power = models.PositiveIntegerField('Мощность (л.с.)', null=True, blank=True)
    transmission = models.CharField('КПП', max_length=20, choices=TRANSMISSION_CHOICES, blank=True)
    fuel_type = models.CharField('Топливо', max_length=20, choices=FUEL_CHOICES, blank=True)
    mileage = models.PositiveIntegerField('Пробег', default=0)

    # Дополнительно
    color = models.CharField('Цвет', max_length=50, blank=True)
    notes = models.TextField('Примечания', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Автомобиль'
        verbose_name_plural = 'Автомобили'
        unique_together = ['client', 'vin']

    def __str__(self):
        return f"{self.brand} {self.model} ({self.license_plate or 'без номера'})"


class Order(models.Model):
    """Модель заказа/ремонта"""

    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('diagnostics', 'Диагностика'),
        ('awaiting_parts', 'Ожидание запчастей'),
        ('in_progress', 'В работе'),
        ('ready', 'Готов к выдаче'),
        ('completed', 'Выполнен'),
        ('cancelled', 'Отменен'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Не оплачен'),
        ('partial', 'Частично оплачен'),
        ('paid', 'Оплачен'),
    ]

    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='orders')
    car = models.ForeignKey(Car, on_delete=models.PROTECT, related_name='orders')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_orders')

    order_number = models.CharField('Номер заказа', max_length=50, unique=True, db_index=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='new', db_index=True)
    payment_status = models.CharField('Статус оплаты', max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')

    # Даты
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    appointment_date = models.DateTimeField('Дата записи', null=True, blank=True)
    completed_at = models.DateTimeField('Дата выполнения', null=True, blank=True)

    # Работы и запчасти
    description = models.TextField('Описание работ')
    master_notes = models.TextField('Заметки мастера', blank=True)

    # Финансы
    labor_cost = models.DecimalField('Стоимость работ', max_digits=10, decimal_places=2, default=0)
    parts_cost = models.DecimalField('Стоимость запчастей', max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField('Общая сумма', max_digits=10, decimal_places=2, default=0)
    prepayment = models.DecimalField('Предоплата', max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField('Скидка', max_digits=10, decimal_places=2, default=0)

    # Гарантия
    warranty_period = models.PositiveIntegerField('Гарантия (дней)', default=30)
    warranty_until = models.DateField('Гарантия до', null=True, blank=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Генерация номера заказа
        if not self.order_number:
            from datetime import datetime
            self.order_number = f"WO-{datetime.now().strftime('%Y%m%d')}-{self.id or 'XXX'}"

        # Расчет общей суммы
        self.total_amount = self.labor_cost + self.parts_cost - self.discount

        # Расчет гарантии
        if self.completed_at and not self.warranty_until:
            from datetime import timedelta
            self.warranty_until = self.completed_at.date() + timedelta(days=self.warranty_period)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Заказ №{self.order_number} - {self.client}"


class Service(models.Model):
    """Модель услуги/работы"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='services')
    name = models.CharField('Название', max_length=200)
    quantity = models.PositiveIntegerField('Количество', default=1)
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    total = models.DecimalField('Сумма', max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.price
        super().save(*args, **kwargs)


class Part(models.Model):
    """Модель запчасти в заказе"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='parts')
    name = models.CharField('Наименование', max_length=200)
    article = models.CharField('Артикул', max_length=100, blank=True)
    quantity = models.PositiveIntegerField('Количество', default=1)
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    total = models.DecimalField('Сумма', max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.price
        super().save(*args, **kwargs)


class ClientHistory(models.Model):
    """История взаимодействия с клиентом"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='history')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField('Действие', max_length=200)
    description = models.TextField('Описание')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'История'
        verbose_name_plural = 'История клиентов'
        ordering = ['-created_at']