from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from .models import Departments, Postname
from .forms import DepartmentForm, PostnameForm


class DepartmentListView(ListView):
    """Список подразделений"""
    model = Departments
    template_name = 'reference/departments_list.html'
    context_object_name = 'departments'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Departments.objects.filter(is_active=True)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class DepartmentDetailView(DetailView):
    """Детальная информация о подразделении"""
    model = Departments
    template_name = 'reference/departments_detail.html'
    context_object_name = 'department'


class DepartmentCreateView(LoginRequiredMixin, CreateView):
    """Создание нового подразделения"""
    model = Departments
    form_class = DepartmentForm
    template_name = 'reference/departments_form.html'
    success_url = reverse_lazy('reference:departments_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Подразделение успешно создано.')
        return super().form_valid(form)


class DepartmentUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование подразделения"""
    model = Departments
    form_class = DepartmentForm
    template_name = 'reference/departments_form.html'
    success_url = reverse_lazy('reference:departments_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Подразделение успешно обновлено.')
        return super().form_valid(form)


class DepartmentDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление подразделения"""
    model = Departments
    template_name = 'reference/departments_confirm_delete.html'
    success_url = reverse_lazy('reference:departments_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Подразделение успешно удалено.')
        return super().delete(request, *args, **kwargs)


class PostnameListView(ListView):
    """Список должностей"""
    model = Postname
    template_name = 'reference/postname_list.html'
    context_object_name = 'postnames'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Postname.objects.filter(is_active=True)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(description__icontains=search) |
                Q(category__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class PostnameDetailView(DetailView):
    """Детальная информация о должности"""
    model = Postname
    template_name = 'reference/postname_detail.html'
    context_object_name = 'postname'


class PostnameCreateView(LoginRequiredMixin, CreateView):
    """Создание новой должности"""
    model = Postname
    form_class = PostnameForm
    template_name = 'reference/postname_form.html'
    success_url = reverse_lazy('reference:postname_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Должность успешно создана.')
        return super().form_valid(form)


class PostnameUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование должности"""
    model = Postname
    form_class = PostnameForm
    template_name = 'reference/postname_form.html'
    success_url = reverse_lazy('reference:postname_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Должность успешно обновлена.')
        return super().form_valid(form)


class PostnameDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление должности"""
    model = Postname
    template_name = 'reference/postname_confirm_delete.html'
    success_url = reverse_lazy('reference:postname_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Должность успешно удалена.')
        return super().delete(request, *args, **kwargs)


def reference_home(request):
    """Главная страница справочников"""
    departments_count = Departments.objects.filter(is_active=True).count()
    postnames_count = Postname.objects.filter(is_active=True).count()
    context = {
        'departments_count': departments_count,
        'postnames_count': postnames_count,
    }
    return render(request, 'reference/reference_home.html', context)
