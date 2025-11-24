"""
Утилита для парсинга HTML-файлов с информацией о сертификатах
Извлекает данные о сертификатах из HTML-страницы портала УЦ ФК
"""
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup


class HTMLParseError(Exception):
    """Ошибка при парсинге HTML"""
    pass


def parse_certificate_html(html_file) -> List[Dict]:
    """
    Парсит HTML-файл и извлекает список сертификатов
    
    Args:
        html_file: Django FileField или файловый объект с HTML-контентом
    
    Returns:
        Список словарей с данными о сертификатах:
        [{
            'certificate_number': str,  # без пробелов
            'certificate_type_text': str,  # "Сертификат должностного лица" или "Сертификат юридического лица"
            'owner_name': str,  # "Фамилия Имя Отчество"
            'expiry_date': datetime.date,  # из строки "DD.MM.YYYY"
        }, ...]
    
    Raises:
        HTMLParseError: Если не удалось распарсить файл
    """
    try:
        # Читаем содержимое файла
        if hasattr(html_file, 'read'):
            html_file.seek(0)
            content = html_file.read()
            # Если это байты, пробуем декодировать
            if isinstance(content, bytes):
                # Пробуем разные кодировки
                try:
                    content = content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        content = content.decode('windows-1251')
                    except UnicodeDecodeError:
                        content = content.decode('utf-8', errors='ignore')
        else:
            # Если это путь к файлу
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(html_file, 'r', encoding='windows-1251') as f:
                    content = f.read()
        
        # Парсим HTML
        soup = BeautifulSoup(content, 'html.parser')
        
        # Находим все блоки сертификатов
        # Используем CSS селектор для более надежного поиска
        # Ищем div с классом cert-item (может быть с дополнительными классами, например "active")
        cert_items = soup.select('div.cert-item')
        
        # Если не нашли через CSS селектор, пробуем через find_all
        if not cert_items:
            def has_cert_item_class(class_list):
                if not class_list:
                    return False
                if isinstance(class_list, list):
                    return 'cert-item' in class_list
                return 'cert-item' in str(class_list)
            cert_items = soup.find_all('div', class_=has_cert_item_class)
        
        certificates = []
        
        # Логируем количество найденных блоков для отладки
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f'Найдено блоков cert-item: {len(cert_items)}')
        
        for idx, cert_item in enumerate(cert_items):
            try:
                cert_data = _extract_certificate_data(cert_item)
                if cert_data:
                    certificates.append(cert_data)
                else:
                    logger.debug(f'Блок {idx}: данные не извлечены (вернулся None)')
            except Exception as e:
                # Пропускаем записи с ошибками, но продолжаем обработку
                logger.debug(f'Блок {idx}: ошибка при извлечении данных: {str(e)}')
                continue
        
        return certificates
    
    except Exception as e:
        raise HTMLParseError(f"Ошибка при парсинге HTML-файла: {str(e)}")


def _extract_certificate_data(cert_item) -> Optional[Dict]:
    """
    Извлекает данные о сертификате из одного блока
    
    Args:
        cert_item: BeautifulSoup элемент с классом 'cert-item'
    
    Returns:
        Словарь с данными или None, если данные некорректны
    """
    try:
        # Тип сертификата и номер сертификата
        # Путь: div.cert-item-content.contWidth1 > div > div (первый div содержит тип, второй - номер)
        # Используем CSS селектор для поиска элемента с классом contWidth1
        cont_width1 = cert_item.select_one('div.contWidth1')
        if not cont_width1:
            # Пробуем через find_all с проверкой класса
            def has_contwidth1_class(class_list):
                if not class_list:
                    return False
                if isinstance(class_list, list):
                    return 'contWidth1' in class_list
                return 'contWidth1' in str(class_list)
            cont_width1 = cert_item.find('div', class_=has_contwidth1_class)
        
        if not cont_width1:
            return None
        
        # Находим внутренний div
        inner_div = cont_width1.find('div')
        if not inner_div:
            return None
        
        # Тип сертификата находится в первом div внутри inner_div
        type_div = inner_div.find('div')
        if not type_div:
            return None
        
        type_b = type_div.find('b')
        if not type_b:
            return None
        
        cert_type_text = type_b.get_text(strip=True)
        if not cert_type_text:
            return None
        
        # Номер сертификата находится во втором div внутри inner_div
        cert_number_divs = inner_div.find_all('div')
        if len(cert_number_divs) < 2:
            return None
        
        cert_number_div = cert_number_divs[1]
        cert_number_text = cert_number_div.get_text(strip=True)
        
        # Извлекаем номер после "№"
        if '№' in cert_number_text:
            cert_number = cert_number_text.split('№', 1)[1].strip()
        else:
            cert_number = cert_number_text.strip()
        
        # Удаляем пробелы из номера
        cert_number = cert_number.replace(' ', '')
        
        if not cert_number:
            return None
        
        # ФИО владельца
        # Путь: div.cert-item-content.contWidth2 > div.owner-name > b (первый элемент)
        # Используем CSS селектор для поиска элемента с классом contWidth2
        cont_width2 = cert_item.select_one('div.contWidth2')
        if not cont_width2:
            # Пробуем через find_all с проверкой класса
            def has_contwidth2_class(class_list):
                if not class_list:
                    return False
                if isinstance(class_list, list):
                    return 'contWidth2' in class_list
                return 'contWidth2' in str(class_list)
            cont_width2 = cert_item.find('div', class_=has_contwidth2_class)
        
        if not cont_width2:
            return None
        
        owner_name_div = cont_width2.find('div', class_='owner-name')
        if not owner_name_div:
            return None
        
        owner_name_b = owner_name_div.find('b')
        if not owner_name_b:
            return None
        
        owner_name = owner_name_b.get_text(strip=True)
        if not owner_name:
            return None
        
        # Дата окончания срока действия
        # Путь: div.cert-item-content-right > table > tr:nth-child(3) > td > b
        # Используем CSS селектор для поиска элемента с классом cert-item-content-right
        cert_content_right = cert_item.select_one('div.cert-item-content-right')
        if not cert_content_right:
            # Пробуем через find_all с проверкой класса
            def has_content_right_class(class_list):
                if not class_list:
                    return False
                if isinstance(class_list, list):
                    return 'cert-item-content-right' in class_list
                return 'cert-item-content-right' in str(class_list)
            cert_content_right = cert_item.find('div', class_=has_content_right_class)
        
        if not cert_content_right:
            return None
        
        table = cert_content_right.find('table')
        if not table:
            return None
        
        # Ищем строку таблицы, в которой содержится последняя жирная дата
        rows = table.find_all('tr')
        if not rows:
            return None
        
        expiry_b = None
        for row in reversed(rows):
            cells = row.find_all('td')
            for cell in reversed(cells or []):
                expiry_b = cell.find('b')
                if expiry_b and expiry_b.get_text(strip=True):
                    break
            if expiry_b and expiry_b.get_text(strip=True):
                break
        
        if not expiry_b:
            return None
        
        expiry_date_text = expiry_b.get_text(strip=True)
        if not expiry_date_text:
            return None
        
        # Парсим дату из формата "DD.MM.YYYY"
        try:
            expiry_date = datetime.strptime(expiry_date_text, '%d.%m.%Y').date()
        except ValueError:
            # Если не удалось распарсить, пропускаем запись
            return None
        
        return {
            'certificate_number': cert_number,
            'certificate_type_text': cert_type_text,
            'owner_name': owner_name,
            'expiry_date': expiry_date,
        }
    
    except Exception:
        # При любой ошибке возвращаем None
        return None

