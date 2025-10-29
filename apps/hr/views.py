from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, View, CreateView, UpdateView, DeleteView

from .models import Posts, Employees, PositionHistory
from .forms import HireNewEmployeeForm, AssignExistingEmployeeForm, MoveEmployeeForm, PostsForm


@login_required
def hr_home(request):
    """Главная страница управления персоналом"""
    return render(request, 'hr/index.html')


class PostsListView(LoginRequiredMixin, ListView):
    model = Posts
    template_name = 'hr/posts_list.html'
    context_object_name = 'posts'


class PostsDetailView(LoginRequiredMixin, DetailView):
    model = Posts
    template_name = 'hr/posts_detail.html'
    context_object_name = 'post'


class HireNewEmployeeView(LoginRequiredMixin, View):
    def get(self, request, pk):
        post = get_object_or_404(Posts, pk=pk)
        form = HireNewEmployeeForm()
        return render(request, 'hr/actions/hire_new_employee.html', {'form': form, 'post': post})

    def post(self, request, pk):
        post = get_object_or_404(Posts, pk=pk)
        form = HireNewEmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save(commit=True)
            start_date = form.cleaned_data['start_date']
            # назначаем
            post.employee = employee
            post.status = Posts.STATUS_OCCUPIED
            post.full_clean()
            post.save()
            # обновляем статус сотрудника
            employee.is_active = True
            employee.save(update_fields=['is_active'])
            # история
            PositionHistory.objects.create(
                employee=employee,
                post=post,
                action=PositionHistory.ACTION_HIRE,
                start_date=start_date,
            )
            messages.success(request, 'Сотрудник принят и назначен на позицию.')
            return redirect('hr:post_detail', pk=post.pk)
        return render(request, 'hr/actions/hire_new_employee.html', {'form': form, 'post': post})


class AssignExistingEmployeeView(LoginRequiredMixin, View):
    def get(self, request, pk):
        post = get_object_or_404(Posts, pk=pk)
        form = AssignExistingEmployeeForm()
        return render(request, 'hr/actions/assign_existing_employee.html', {'form': form, 'post': post})

    def post(self, request, pk):
        post = get_object_or_404(Posts, pk=pk)
        form = AssignExistingEmployeeForm(request.POST)
        if form.is_valid():
            employee = form.cleaned_data['employee']
            start_date = form.cleaned_data['start_date']
            post.employee = employee
            post.status = Posts.STATUS_OCCUPIED
            post.full_clean()
            post.save()
            employee.is_active = True
            employee.save(update_fields=['is_active'])
            PositionHistory.objects.create(
                employee=employee,
                post=post,
                action=PositionHistory.ACTION_RETURN,
                start_date=start_date,
            )
            messages.success(request, 'Сотрудник возвращен на позицию.')
            return redirect('hr:post_detail', pk=post.pk)
        return render(request, 'hr/actions/assign_existing_employee.html', {'form': form, 'post': post})


class MoveEmployeeView(LoginRequiredMixin, View):
    def get(self, request, pk):
        post = get_object_or_404(Posts, pk=pk)
        form = MoveEmployeeForm()
        return render(request, 'hr/actions/move_employee.html', {'form': form, 'post': post})

    def post(self, request, pk):
        source_post = get_object_or_404(Posts, pk=pk)
        form = MoveEmployeeForm(request.POST)
        if form.is_valid():
            target_post = form.cleaned_data['target_post']
            start_date = form.cleaned_data['start_date']

            employee = source_post.employee
            if not employee:
                messages.error(request, 'На исходной позиции нет сотрудника.')
                return redirect('hr:post_detail', pk=source_post.pk)

            # закрываем историю по source
            PositionHistory.objects.filter(employee=employee, post=source_post, end_date__isnull=True).update(end_date=start_date)
            # освобождаем source
            source_post.employee = None
            source_post.status = Posts.STATUS_VACANT
            source_post.save()

            # назначаем в target
            target_post.employee = employee
            target_post.status = Posts.STATUS_OCCUPIED
            target_post.full_clean()
            target_post.save()

            PositionHistory.objects.create(
                employee=employee,
                post=target_post,
                action=PositionHistory.ACTION_MOVE,
                start_date=start_date,
            )

            messages.success(request, 'Сотрудник перемещен на новую позицию.')
            return redirect('hr:post_detail', pk=target_post.pk)
        return render(request, 'hr/actions/move_employee.html', {'form': form, 'post': source_post})


class FreePositionView(LoginRequiredMixin, View):
    def post(self, request, pk):
        post = get_object_or_404(Posts, pk=pk)
        employee = post.employee
        if not employee:
            messages.info(request, 'Позиция уже вакантна.')
            return redirect('hr:post_detail', pk=pk)

        # прекращаем активную запись history
        PositionHistory.objects.filter(employee=employee, post=post, end_date__isnull=True).update(end_date=request.POST.get('end_date'))

        # увольняем: позицию освобождаем, сотрудника делаем неактивным
        post.employee = None
        post.status = Posts.STATUS_VACANT
        post.save()

        employee.is_active = False
        employee.save(update_fields=['is_active'])

        PositionHistory.objects.create(
            employee=employee,
            post=post,
            action=PositionHistory.ACTION_DISMISS,
            start_date=request.POST.get('end_date'),
            end_date=request.POST.get('end_date'),
        )

        messages.success(request, 'Позиция освобождена, сотрудник уволен.')
        return redirect('hr:post_detail', pk=pk)


class EmployeesListView(LoginRequiredMixin, ListView):
    model = Employees
    template_name = 'hr/employees_list.html'
    context_object_name = 'employees'
    paginate_by = 20


class EmployeeDetailView(LoginRequiredMixin, DetailView):
    model = Employees
    template_name = 'hr/employee_detail.html'
    context_object_name = 'employee'


class EmployeeCreateView(LoginRequiredMixin, CreateView):
    model = Employees
    from .forms import EmployeesForm
    form_class = EmployeesForm
    template_name = 'hr/employee_form.html'
    success_url = reverse_lazy('hr:employees')

    def form_valid(self, form):
        messages.success(self.request, 'Сотрудник успешно создан.')
        return super().form_valid(form)


class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employees
    from .forms import EmployeesForm
    form_class = EmployeesForm
    template_name = 'hr/employee_form.html'
    success_url = reverse_lazy('hr:employees')

    def form_valid(self, form):
        messages.success(self.request, 'Сотрудник успешно обновлен.')
        return super().form_valid(form)


class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    model = Employees
    template_name = 'hr/employee_confirm_delete.html'
    success_url = reverse_lazy('hr:employees')

    def post(self, request, *args, **kwargs):
        messages.success(request, 'Сотрудник успешно удален.')
        return super().post(request, *args, **kwargs)


class PositionHistoryListView(LoginRequiredMixin, ListView):
    model = PositionHistory
    template_name = 'hr/history_list.html'
    context_object_name = 'history'
    paginate_by = 25
    ordering = ['-start_date', '-created_at']

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Posts
    form_class = PostsForm
    template_name = 'hr/post_form.html'
    success_url = reverse_lazy('hr:posts')

    def form_valid(self, form):
        # Новая позиция по умолчанию вакантна
        form.instance.status = Posts.STATUS_VACANT
        messages.success(self.request, 'Штатная позиция создана.')
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Posts
    form_class = PostsForm
    template_name = 'hr/post_form.html'
    success_url = reverse_lazy('hr:posts')

    def form_valid(self, form):
        messages.success(self.request, 'Штатная позиция обновлена.')
        return super().form_valid(form)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Posts
    template_name = 'hr/post_confirm_delete.html'
    success_url = reverse_lazy('hr:posts')

    def post(self, request, *args, **kwargs):
        messages.success(request, 'Штатная позиция удалена.')
        return super().post(request, *args, **kwargs)


