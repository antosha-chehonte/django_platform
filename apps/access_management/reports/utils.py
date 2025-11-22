from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from apps.access_management.models import SystemAccess, DigitalSignature
from apps.hr.models import Employees, Posts


def get_employee_department(employee):
    """
    Получить текущее подразделение сотрудника через активную должность
    Возвращает Departments или None
    """
    current_post = Posts.objects.filter(
        employee=employee,
        status=Posts.STATUS_OCCUPIED,
        is_active=True
    ).select_related('department').first()
    
    return current_post.department if current_post else None


def get_system_accesses_by_department(system_id, status='active', department_id=None):
    """
    Получить доступы к системе, сгруппированные по подразделениям
    
    Returns:
        dict: {department: [accesses]}
    """
    accesses = SystemAccess.objects.filter(
        system_id=system_id,
        status=status
    ).select_related('employee', 'system')
    
    if department_id:
        # Фильтр по подразделению
        accesses = accesses.filter(
            employee__posts__department_id=department_id,
            employee__posts__status=Posts.STATUS_OCCUPIED
        )
    
    # Группировка по подразделениям
    result = {}
    for access in accesses:
        department = get_employee_department(access.employee)
        dept_name = department.name if department else "Не указано"
        
        if dept_name not in result:
            result[dept_name] = []
        
        post = Posts.objects.filter(
            employee=access.employee,
            status=Posts.STATUS_OCCUPIED,
            is_active=True
        ).select_related('postname', 'department').first()
        
        result[dept_name].append({
            'access': access,
            'department': department,
            'employee': access.employee,
            'post': post
        })
    
    return result


def get_expiring_accesses(days=40, status_filter=None):
    """
    Получить доступы, требующие актуализации или истекающие
    
    Args:
        days: количество дней для определения "истекающих"
        status_filter: список типов фильтров (None = все требующие внимания)
    
    Returns:
        list: список доступов с дополнительной информацией
    """
    today = timezone.now().date()
    future_date = today + timedelta(days=days)
    
    q_objects = Q()
    
    # Доступы со статусом "требует актуализации"
    if status_filter is None or 'needs_update' in status_filter:
        q_objects |= Q(status=SystemAccess.STATUS_NEEDS_UPDATE)
    
    # Доступы с датой блокировки в прошлом (просроченные)
    if status_filter is None or 'expired' in status_filter:
        q_objects |= Q(
            access_blocked_date__lt=today,
            access_blocked_date__isnull=False,
            status__in=[SystemAccess.STATUS_ACTIVE, SystemAccess.STATUS_SUSPENDED]
        )
    
    # Доступы с датой блокировки в ближайшие N дней (истекающие)
    if status_filter is None or 'expiring' in status_filter:
        q_objects |= Q(
            access_blocked_date__gte=today,
            access_blocked_date__lte=future_date,
            access_blocked_date__isnull=False,
            status__in=[SystemAccess.STATUS_ACTIVE, SystemAccess.STATUS_SUSPENDED]
        )
    
    if not q_objects:
        return []
    
    accesses = SystemAccess.objects.filter(q_objects).select_related(
        'employee', 'system'
    )
    
    result = []
    for access in accesses:
        department = get_employee_department(access.employee)
        post = Posts.objects.filter(
            employee=access.employee,
            status=Posts.STATUS_OCCUPIED,
            is_active=True
        ).select_related('postname', 'department').first()
        
        # Расчет дней до/после блокировки
        days_diff = None
        if access.access_blocked_date:
            days_diff = (access.access_blocked_date - today).days
        
        result.append({
            'access': access,
            'department': department,
            'employee': access.employee,
            'post': post,
            'days_diff': days_diff,
            'abs_days_diff': abs(days_diff) if days_diff is not None else None,
            'is_expired': days_diff < 0 if days_diff is not None else False
        })
    
    return result


def get_employees_with_signature(status='active', cert_type_id=None, department_id=None):
    """
    Получить сотрудников с активной цифровой подписью, сгруппированных по подразделениям
    
    Returns:
        dict: {department: [signatures]}
    """
    signatures = DigitalSignature.objects.filter(status=status).select_related(
        'employee', 'certificate_type'
    )
    
    if cert_type_id:
        signatures = signatures.filter(certificate_type_id=cert_type_id)
    
    if department_id:
        signatures = signatures.filter(
            employee__posts__department_id=department_id,
            employee__posts__status=Posts.STATUS_OCCUPIED
        )
    
    result = {}
    for signature in signatures:
        department = get_employee_department(signature.employee)
        dept_name = department.name if department else "Не указано"
        
        if dept_name not in result:
            result[dept_name] = []
        
        post = Posts.objects.filter(
            employee=signature.employee,
            status=Posts.STATUS_OCCUPIED,
            is_active=True
        ).select_related('postname', 'department').first()
        
        result[dept_name].append({
            'signature': signature,
            'department': department,
            'employee': signature.employee,
            'post': post
        })
    
    return result


def get_employees_without_signature(department_id=None, active_only=True):
    """
    Получить сотрудников без активной цифровой подписи
    
    Returns:
        dict: {department: [employees]}
    """
    # Найти сотрудников по статусу
    if active_only:
        # Только активные сотрудники (исключаем уволенных и временно отсутствующих)
        employees = Employees.objects.filter(status=Employees.STATUS_ACTIVE)
    else:
        # Все сотрудники, включая уволенных и временно отсутствующих
        employees = Employees.objects.all()
    
    if department_id:
        employees = employees.filter(
            posts__department_id=department_id,
            posts__status=Posts.STATUS_OCCUPIED
        ).distinct()
    
    # Исключить тех, у кого есть активная подпись
    employees_with_signature = DigitalSignature.objects.filter(
        status=DigitalSignature.STATUS_ACTIVE
    ).values_list('employee_id', flat=True)
    
    employees = employees.exclude(id__in=employees_with_signature)
    
    # Группировка по подразделениям
    result = {}
    for employee in employees:
        department = get_employee_department(employee)
        dept_name = department.name if department else "Не указано"
        
        if dept_name not in result:
            result[dept_name] = []
        
        post = Posts.objects.filter(
            employee=employee,
            status=Posts.STATUS_OCCUPIED,
            is_active=True
        ).select_related('postname', 'department').first()
        
        result[dept_name].append({
            'employee': employee,
            'department': department,
            'post': post
        })
    
    return result


def get_expiring_signatures(days=40, active_only=True, department_id=None):
    """
    Получить сертификаты, срок действия которых истекает в ближайшие N дней
    
    Returns:
        list: список подписей с дополнительной информацией
    """
    today = timezone.now().date()
    future_date = today + timedelta(days=days)
    
    signatures = DigitalSignature.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=future_date
    )
    
    if active_only:
        signatures = signatures.filter(status=DigitalSignature.STATUS_ACTIVE)
    
    if department_id:
        signatures = signatures.filter(
            employee__posts__department_id=department_id,
            employee__posts__status=Posts.STATUS_OCCUPIED
        )
    
    signatures = signatures.select_related('employee', 'certificate_type')
    
    result = []
    for signature in signatures:
        department = get_employee_department(signature.employee)
        post = Posts.objects.filter(
            employee=signature.employee,
            status=Posts.STATUS_OCCUPIED,
            is_active=True
        ).select_related('postname', 'department').first()
        
        days_diff = (signature.expiry_date - today).days
        
        result.append({
            'signature': signature,
            'department': department,
            'employee': signature.employee,
            'post': post,
            'days_diff': days_diff
        })
    
    return result

