"""
Утилита для парсинга файлов сертификатов (.cer, .pfx)
Извлекает информацию из X.509 сертификатов для автоматического заполнения модели DigitalSignature
"""
import hashlib
from datetime import datetime
from typing import Dict, Optional, Tuple
from io import BytesIO

try:
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.serialization import pkcs12
except ImportError:
    x509 = None
    default_backend = None
    serialization = None
    hashes = None
    pkcs12 = None


class CertificateParseError(Exception):
    """Ошибка при парсинге сертификата"""
    pass


def parse_certificate_file(file_content: bytes, filename: str = None) -> Dict[str, any]:
    """
    Парсит файл сертификата (.cer или .pfx) и извлекает информацию
    
    Args:
        file_content: Содержимое файла в байтах
        filename: Имя файла (опционально, для определения формата)
    
    Returns:
        Словарь с извлеченными данными:
        {
            'certificate_serial': str,  # Серийный номер сертификата
            'certificate_alias': str,   # Отпечаток (SHA-1 fingerprint, без пробелов)
            'expiry_date': datetime.date,  # Дата окончания действия
            'valid_from': datetime.date,    # Дата начала действия
            'subject_name': str,  # ФИО из Subject (CN или SN+GN)
            'issuer_name': str,  # Издатель сертификата
            'subject_attributes': dict,  # Все атрибуты Subject
        }
    
    Raises:
        CertificateParseError: Если не удалось распарсить файл
    """
    if x509 is None:
        raise CertificateParseError(
            "Библиотека cryptography не установлена. "
            "Установите её: pip install cryptography"
        )
    
    try:
        # Определяем формат файла
        cert = None
        
        # Пробуем распарсить как PEM
        if file_content.startswith(b'-----BEGIN'):
            cert = _parse_pem(file_content)
        
        # Пробуем распарсить как DER (бинарный формат .cer)
        elif filename and filename.lower().endswith('.cer'):
            cert = _parse_der(file_content)
        
        # Пробуем распарсить как PKCS12 (.pfx)
        elif filename and filename.lower().endswith('.pfx'):
            cert = _parse_pfx(file_content)
        
        # Если формат не определен, пробуем DER
        else:
            try:
                cert = _parse_der(file_content)
            except Exception:
                # Если не получилось, пробуем PEM
                try:
                    cert = _parse_pem(file_content)
                except Exception:
                    raise CertificateParseError("Не удалось определить формат сертификата")
        
        if cert is None:
            raise CertificateParseError("Не удалось загрузить сертификат")
        
        # Извлекаем данные из сертификата
        return _extract_certificate_data(cert)
    
    except CertificateParseError:
        raise
    except Exception as e:
        raise CertificateParseError(f"Ошибка при парсинге сертификата: {str(e)}")


def _parse_pem(content: bytes) -> x509.Certificate:
    """Парсит сертификат в формате PEM"""
    try:
        return x509.load_pem_x509_certificate(content, default_backend())
    except Exception as e:
        raise CertificateParseError(f"Ошибка парсинга PEM: {str(e)}")


def _parse_der(content: bytes) -> x509.Certificate:
    """Парсит сертификат в формате DER (бинарный)"""
    try:
        return x509.load_der_x509_certificate(content, default_backend())
    except Exception as e:
        raise CertificateParseError(f"Ошибка парсинга DER: {str(e)}")


def _parse_pfx(content: bytes, password: bytes = None) -> x509.Certificate:
    """
    Парсит сертификат в формате PKCS12 (.pfx)
    
    Note: Для .pfx файлов может потребоваться пароль
    """
    try:
        private_key, cert, additional_certs = pkcs12.load_key_and_certificates(
            content, password, backend=default_backend()
        )
        if cert is None:
            raise CertificateParseError("В PKCS12 файле не найден сертификат")
        return cert
    except Exception as e:
        if "password" in str(e).lower() or "decryption" in str(e).lower():
            raise CertificateParseError("Для .pfx файла требуется пароль")
        raise CertificateParseError(f"Ошибка парсинга PKCS12: {str(e)}")


def _extract_certificate_data(cert: x509.Certificate) -> Dict[str, any]:
    """Извлекает данные из объекта сертификата"""
    
    if hashes is None:
        raise CertificateParseError("Модуль hashes не импортирован. Проверьте установку библиотеки cryptography.")
    
    # Серийный номер
    serial_number = format(cert.serial_number, 'X')  # Шестнадцатеричный формат
    
    # Отпечаток (SHA-1 fingerprint)
    # Используем правильный класс хеша из cryptography
    fingerprint = cert.fingerprint(hashes.SHA1())
    fingerprint_hex = fingerprint.hex().upper()
    # Отпечаток без пробелов
    fingerprint_formatted = fingerprint_hex
    
    # Даты действия
    not_valid_after = cert.not_valid_after.date()
    not_valid_before = cert.not_valid_before.date()
    
    # Извлекаем информацию о субъекте
    subject = cert.subject
    subject_attributes = {}
    for attr in subject:
        subject_attributes[attr.oid._name] = attr.value
    
    # Извлекаем ФИО из Subject
    # Обычно в поле CN (Common Name) или в отдельных полях SN (Surname), GN (Given Name)
    subject_name = None
    if 'commonName' in subject_attributes:
        subject_name = subject_attributes['commonName']
    elif 'surname' in subject_attributes and 'givenName' in subject_attributes:
        surname = subject_attributes.get('surname', '')
        given_name = subject_attributes.get('givenName', '')
        # Может быть и middle name
        if 'initials' in subject_attributes:
            subject_name = f"{surname} {given_name} {subject_attributes['initials']}"
        else:
            subject_name = f"{surname} {given_name}"
    
    # Издатель
    issuer = cert.issuer
    issuer_name = None
    for attr in issuer:
        if attr.oid._name == 'commonName':
            issuer_name = attr.value
            break
    
    return {
        'certificate_serial': serial_number,
        'certificate_alias': fingerprint_formatted,
        'expiry_date': not_valid_after,
        'valid_from': not_valid_before,
        'subject_name': subject_name,
        'issuer_name': issuer_name,
        'subject_attributes': subject_attributes,
    }


def parse_certificate_from_django_file(file_field) -> Dict[str, any]:
    """
    Удобная функция для парсинга файла из Django FileField
    
    Args:
        file_field: Django FileField или InMemoryUploadedFile
    
    Returns:
        Словарь с извлеченными данными (см. parse_certificate_file)
    """
    if not file_field:
        raise CertificateParseError("Файл не предоставлен")
    
    # Читаем содержимое файла
    if hasattr(file_field, 'read'):
        file_field.seek(0)  # Перемещаемся в начало файла
        content = file_field.read()
        filename = getattr(file_field, 'name', None)
    else:
        # Если это путь к файлу
        with open(file_field, 'rb') as f:
            content = f.read()
        filename = str(file_field)
    
    return parse_certificate_file(content, filename)


def get_certificate_thumbprint(file_content: bytes) -> str:
    """
    Получает только отпечаток (thumbprint) сертификата
    
    Args:
        file_content: Содержимое файла в байтах
    
    Returns:
        Отпечаток в формате hex (верхний регистр, без пробелов)
    """
    data = parse_certificate_file(file_content)
    return data['certificate_alias']

