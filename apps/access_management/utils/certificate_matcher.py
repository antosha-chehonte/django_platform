"""
Утилита для сопоставления данных сертификатов с существующими записями в БД
"""
from typing import Optional
from apps.hr.models import Employees
from apps.reference.models import CertificateType
from apps.access_management.models import DigitalSignature


def get_certificate_type_by_text(type_text: str) -> Optional[CertificateType]:
    """
    Получает объект CertificateType по тексту из HTML
    
    Args:
        type_text: Текст типа сертификата из HTML
                  ("Сертификат должностного лица" или "Сертификат юридического лица")
    
    Returns:
        Объект CertificateType или None, если тип не найден
    """
    try:
        # Нормализуем текст (убираем лишние пробелы)
        type_text = type_text.strip()
        
        # Ищем точное совпадение по названию
        cert_type = CertificateType.objects.filter(
            name=type_text,
            is_active=True
        ).first()
        
        return cert_type
    except Exception:
        return None


def match_employee_by_name(full_name: str) -> Optional[Employees]:
    """
    Ищет сотрудника по полному ФИО
    
    Args:
        full_name: Полное ФИО в формате "Фамилия Имя Отчество"
    
    Returns:
        Объект Employees, если найден один сотрудник
        None, если не найден или найдено несколько
    """
    try:
        # Нормализуем ФИО (убираем лишние пробелы)
        full_name = ' '.join(full_name.split())
        
        # Разбиваем ФИО на части
        name_parts = full_name.split()
        
        if len(name_parts) < 2:
            # Минимум фамилия и имя
            return None
        
        last_name = name_parts[0].strip()
        first_name = name_parts[1].strip()
        middle_name = name_parts[2].strip() if len(name_parts) > 2 else ''
        
        # Поиск с учетом регистра и пробелов
        query = Employees.objects.filter(
            last_name__iexact=last_name,
            first_name__iexact=first_name
        )
        
        # Если есть отчество, добавляем его в фильтр
        if middle_name:
            query = query.filter(middle_name__iexact=middle_name)
        else:
            # Если отчества нет, ищем записи с пустым отчеством
            query = query.filter(middle_name__in=['', None])
        
        # Получаем результаты
        employees = list(query)
        
        if len(employees) == 1:
            return employees[0]
        elif len(employees) == 0:
            return None
        else:
            # Найдено несколько сотрудников - возвращаем None
            # (в будущем можно добавить логику выбора)
            return None
    
    except Exception:
        return None


def check_duplicate_certificate(certificate_serial: str) -> bool:
    """
    Проверяет, существует ли уже сертификат с таким серийным номером
    
    Args:
        certificate_serial: Серийный номер сертификата
    
    Returns:
        True, если дубликат найден, False если нет
    """
    try:
        # Нормализуем номер (убираем пробелы, приводим к верхнему регистру)
        certificate_serial = certificate_serial.strip().upper().replace(' ', '')
        
        # Ищем точное совпадение
        exists = DigitalSignature.objects.filter(
            certificate_serial__iexact=certificate_serial
        ).exists()
        
        return exists
    except Exception:
        # При ошибке считаем, что дубликата нет
        return False

