# apps_testing/tests/templatetags/test_filters.py
from django import template

register = template.Library()


@register.filter
def test_duration(start_time, end_time):
    """
    Вычисляет и форматирует длительность теста в формате "X мин. Y сек."
    Использование: {{ session.start_time|test_duration:session.end_time }}
    """
    if not start_time or not end_time:
        return "Не определено"
    
    try:
        duration = end_time - start_time
        total_seconds = int(duration.total_seconds())
        
        if total_seconds < 0:
            return "Не определено"
        
        if total_seconds == 0:
            return "0 сек."
        
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        
        if minutes > 0:
            if seconds > 0:
                return f"{minutes} мин. {seconds} сек."
            else:
                return f"{minutes} мин."
        else:
            return f"{seconds} сек."
    except (TypeError, AttributeError):
        return "Не определено"

