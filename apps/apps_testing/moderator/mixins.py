# apps_testing/moderator/mixins.py
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
import logging

logger = logging.getLogger('moderator_actions')

class ModeratorRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_staff:
            return redirect('test_list')
        return super().dispatch(request, *args, **kwargs)


class LogCreateUpdateMixin:
    """
    Миксин для логирования действий СОЗДАНИЯ и ОБНОВЛЕНИЯ.
    Безопасно используется с CreateView и UpdateView.
    """
    def form_valid(self, form):
        action = "создал" if self.object is None else "обновил"
        logger.info(
            f"Модератор '{self.request.user.username}' {action} объект "
            f"'{form.instance}' модели '{form.instance.__class__.__name__}'."
        )
        return super().form_valid(form)


class LogDeleteMixin:
    """
    Миксин для логирования действий УДАЛЕНИЯ.
    Безопасно используется с DeleteView.
    """
    def delete(self, request, *args, **kwargs):
        # self.object устанавливается родительским классом DeleteView
        self.object = self.get_object()
        logger.info(
            f"Модератор '{request.user.username}' удалил объект "
            f"'{self.object}' модели '{self.object.__class__.__name__}'."
        )
        # Важно вызвать super().delete для выполнения фактического удаления
        return super().delete(request, *args, **kwargs)
