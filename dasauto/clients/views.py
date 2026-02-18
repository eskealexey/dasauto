# # Create your views here.

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum, Value, DecimalField, IntegerField, F
from django.db.models.functions import Coalesce
from django.http import JsonResponse, Http404
from django.utils import timezone
from datetime import datetime, timedelta

from .forms import ClientForm
from .models import Client, Car, Order, ClientHistory


@login_required
def client_list(request):
    # Фильтруем клиентов по текущему пользователю (поле created_by)
    clients = Client.objects.filter(
        is_active=True,
        created_by=request.user  # Используем created_by вместо user
    ).annotate(
        orders_count=Coalesce(
            Count('orders', distinct=True),
            Value(0),
            output_field=IntegerField()
        ),
        total_spent_sum=Coalesce(
            Sum('orders__total_amount'),
            Value(0),
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )
    ).select_related('created_by').prefetch_related('cars')

    # Поиск
    query = request.GET.get('q')
    if query:
        clients = clients.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(patronymic__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query) |
            Q(company_name__icontains=query) |
            Q(inn__icontains=query)
        )

    # Фильтры
    client_type = request.GET.get('client_type')
    if client_type:
        clients = clients.filter(client_type=client_type)

    # Сортировка
    sort_by = request.GET.get('sort', '-created_at')
    clients = clients.order_by(sort_by)

    # Пагинация
    paginator = Paginator(clients, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'clients': page_obj,
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1,
        'total_clients': Client.objects.filter(is_active=True, created_by=request.user).count(),
        'query': query,
        'client_type': client_type,
        'sort_by': sort_by,
    }

    return render(request, 'clients/client_list.html', context)


@login_required
def client_detail(request, pk):
    # Используем filter с created_by=request.user, а потом get
    try:
        client = Client.objects.filter(created_by=request.user).get(pk=pk)
    except Client.DoesNotExist:
        raise Http404("Клиент не найден или у вас нет доступа к нему")

    # Аннотируем клиента дополнительными полями
    client = Client.objects.filter(pk=client.pk).annotate(
        orders_count=Coalesce(
            Count('orders', distinct=True),
            Value(0),
            output_field=IntegerField()
        ),
        total_spent_sum=Coalesce(
            Sum('orders__total_amount'),
            Value(0),
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )
    ).first()

    cars = client.cars.all()
    orders = client.orders.all().order_by('-created_at')
    history = client.history.all()[:20]

    # Статистика по заказам
    orders_stats = {
        'total': orders.count(),
        'completed': orders.filter(status='completed').count(),
        'in_progress': orders.exclude(status__in=['completed', 'cancelled']).count(),
        'total_amount': orders.aggregate(
            total=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField(max_digits=10, decimal_places=2))
        )['total'] or 0,
    }

    context = {
        'client': client,
        'cars': cars,
        'orders': orders,
        'history': history,
        'orders_stats': orders_stats,
    }
    return render(request, 'clients/client_detail.html', context)


@login_required
def dashboard(request):
    """Дашборд для автомастерской с фильтрацией по текущему пользователю"""

    today = timezone.now().date()

    # Статистика за сегодня
    orders_today = Order.objects.filter(
        created_at__date=today,
        client__created_by=request.user  # Используем client__created_by
    ).count()

    orders_in_progress = Order.objects.filter(
        client__created_by=request.user  # Используем client__created_by
    ).exclude(
        status__in=['completed', 'cancelled']
    ).count()

    # Топ клиентов текущего пользователя
    top_clients = Client.objects.filter(
        created_by=request.user  # Используем created_by
    ).annotate(
        total_orders=Coalesce(
            Count('orders', distinct=True),
            Value(0),
            output_field=IntegerField()
        ),
        total_sum=Coalesce(
            Sum('orders__total_amount'),
            Value(0),
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )
    ).order_by('-total_sum')[:10]

    # Заказы по статусам
    orders_by_status = Order.objects.filter(
        client__created_by=request.user  # Используем client__created_by
    ).values('status').annotate(
        count=Coalesce(
            Count('id'),
            Value(0),
            output_field=IntegerField()
        )
    )

    # Предстоящие записи
    upcoming_appointments = Order.objects.filter(
        appointment_date__date__gte=today,
        client__created_by=request.user,  # Используем client__created_by
        status__in=['new', 'diagnostics']
    ).select_related('client', 'car').order_by('appointment_date')[:10]

    # Для преобразования статусов в читаемый вид
    for item in orders_by_status:
        item['status_display'] = dict(Order.STATUS_CHOICES).get(item['status'], item['status'])

    context = {
        'orders_today': orders_today,
        'orders_in_progress': orders_in_progress,
        'top_clients': top_clients,
        'orders_by_status': orders_by_status,
        'upcoming_appointments': upcoming_appointments,
    }
    return render(request, 'clients/dashboard.html', context)


@login_required
def get_client_cars(request, client_id):
    """API для получения автомобилей клиента"""
    # Проверяем, что клиент принадлежит текущему пользователю
    client = get_object_or_404(Client, id=client_id, created_by=request.user)
    cars = Car.objects.filter(client=client).values('id', 'brand', 'model', 'license_plate')
    return JsonResponse(list(cars), safe=False)


@login_required
def get_client_cars(request, client_id):
    """API для получения автомобилей клиента"""
    # Проверяем, что клиент принадлежит текущему пользователю
    client = get_object_or_404(Client, id=client_id, user=request.user)
    cars = Car.objects.filter(client=client).values('id', 'brand', 'model', 'license_plate')
    return JsonResponse(list(cars), safe=False)


@login_required
def client_create(request):
    if request.method == 'POST':
        print("POST request received")
        print(f"POST data: {request.POST}")

        form = ClientForm(request.POST)

        if form.is_valid():
            print("Form is valid")
            print(f"Cleaned data: {form.cleaned_data}")

            client = form.save(commit=False)
            client.is_active = True
            client.created_by = request.user
            print(f"Client before save: {client}")
            print(f"Created by: {client.created_by}")

            client.save()
            print(f"Client after save, ID: {client.id}")

            # Добавляем запись в историю
            history = ClientHistory.objects.create(
                client=client,
                created_by=request.user,
                action='Создание клиента',
                description=f'Клиент создан пользователем {request.user.username}'
            )
            print(f"History created: {history.id}")

            messages.success(request, f'Клиент {client.last_name} {client.first_name} успешно добавлен!')
            return redirect('client_list')
        else:
            print(f"Form errors: {form.errors}")
            messages.error(request, 'Проверьте данные формы. Пожалуйста, исправьте ошибки ниже.')
    else:
        form = ClientForm()

    return render(request, 'clients/client_form.html', {
        'form': form,
        'title': 'Добавить клиента'
    })

@login_required
def client_edit(request, pk):
    # Проверяем, что клиент принадлежит текущему пользователю
    client = get_object_or_404(Client, pk=pk, created_by=request.user)

    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            client = form.save()

            # Добавляем запись в историю
            ClientHistory.objects.create(
                client=client,
                created_by=request.user,
                action='Редактирование клиента',
                description=f'Данные клиента обновлены пользователем {request.user.username}'
            )

            messages.success(request, f'Данные клиента {client.last_name} {client.first_name} успешно обновлены!')
            return redirect('client_detail', pk=client.pk)
        else:
            messages.error(request, 'Проверьте данные формы. Пожалуйста, исправьте ошибки ниже.')
    else:
        form = ClientForm(instance=client)

    return render(request, 'clients/client_form.html', {
        'form': form,
        'client': client,
        'title': f'Редактировать клиента: {client.last_name} {client.first_name}'
    })


# from django.shortcuts import render
# from django.contrib.auth.decorators import login_required
# from .models import Client, Order  # Предполагается, что модели существуют

@login_required
def clients_dashboard_view(request):
    # Начальные данные для статистики
    orders_today = Order.objects.filter(created_at__date=timezone.now().date()).count()
    orders_in_progress = Order.objects.filter(status='in_progress').count()
    top_clients = Client.objects.order_by('-total_orders')[:5]
    upcoming_appointments = Order.objects.filter(
        appointment_date__gte=timezone.now()
    ).order_by('appointment_date')[:5]

    # Поиск клиентов
    clients = Client.objects.all()
    last_name = request.GET.get('last_name')
    phone = request.GET.get('phone')
    additional_phone = request.GET.get('additional_phone')

    if last_name:
        clients = clients.filter(last_name__icontains=last_name.strip())
    if phone:
        clients = clients.filter(phone__icontains=phone.strip())
    if additional_phone:
        clients = clients.filter(additional_phone__icontains=additional_phone.strip())

    # Передаём отфильтрованных клиентов в контекст (если нужно отображать список)
    # Например: 'search_results': clients[:20] — первые 20 результатов

    context = {
        'orders_today': orders_today,
        'orders_in_progress': orders_in_progress,
        'top_clients': top_clients,
        'upcoming_appointments': upcoming_appointments,
        # Раскомментируйте, если нужно показать результаты поиска
        # 'search_results': clients[:20],
    }
    return render(request, 'clients/dashboard.html', context)