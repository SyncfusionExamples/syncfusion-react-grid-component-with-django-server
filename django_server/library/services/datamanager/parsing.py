
# services/datamanager/parsing.py
import json
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Optional

from django.db import models


def to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ('true', '1', 'yes', 'y')
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def json_or_value(maybe_json: Any) -> Any:
    if isinstance(maybe_json, str):
        try:
            return json.loads(maybe_json)
        except Exception:
            return maybe_json
    return maybe_json

def normalize_operator(raw_operator: Optional[str]) -> str:
    if not raw_operator:
        return ''
    name = raw_operator.strip().lower()
    return {
        # equality
        'equal': 'equal', '==': 'equal', 'eq': 'equal',
        'notequal': 'notequal', '!=': 'notequal', 'ne': 'notequal',

        # comparisons
        'greaterthan': 'gt', 'gt': 'gt', '>': 'gt',
        'greaterthanorequal': 'gte', 'ge': 'gte', '>=': 'gte',
        'lessthan': 'lt', 'lt': 'lt', '<': 'lt',
        'lessthanorequal': 'lte', 'le': 'lte', '<=': 'lte',

        # string positives
        'contains': 'contains',
        'startswith': 'startswith',
        'endswith': 'endswith',
        'like': 'like',

        # string negatives (aliases included)
        'doesnotcontain': 'notcontains', 'notcontains': 'notcontains',
        'doesnotstartwith': 'notstartswith',
        'doesnotendwith': 'notendswith',

        # collections
        'in': 'in', 'notin': 'notin',
        'between': 'between',

        # null / empty (aliases included)
        'isnull': 'isnull',
        'isnotnull': 'isnotnull', 'notnull': 'isnotnull',
        'isempty': 'isempty',
        'isnotempty': 'isnotempty',
    }.get(name, name)

# ---------- NEW: type coercion ----------

def _parse_iso_datetime(value: str) -> datetime:
    # Accept '...Z' (UTC) by replacing with '+00:00'
    if isinstance(value, str) and value.endswith('Z'):
        value = value[:-1] + '+00:00'
    # fromisoformat handles 'YYYY-MM-DD' and full ISO-8601 with offset
    return datetime.fromisoformat(value)


def coerce_value_for_field(model: type[models.Model], field_name: str, raw_value: Any) -> Any:
    """
    Convert raw payload values to appropriate Python types for the Django field.
    - DateTimeField: ISO 8601 → datetime
    - DateField: ISO 8601 → date
    - Integer/Float/Decimal/Boolean/UUID
    - For arrays (in/between), coerce each element
    """
    if raw_value is None:
        return None

    # If field doesn't exist (annotation or dynamic), return as-is
    try:
        field = model._meta.get_field(field_name)
    except Exception:
        return raw_value

    # Handle arrays (for __in, between)
    if isinstance(raw_value, (list, tuple)):
        return [coerce_value_for_field(model, field_name, v) for v in raw_value]

    # Primitive coercions by field type
    try:
        if isinstance(field, (models.DateTimeField,)):
            if isinstance(raw_value, datetime):
                return raw_value
            if isinstance(raw_value, str):
                return _parse_iso_datetime(raw_value)

        if isinstance(field, (models.DateField,)):
            if isinstance(raw_value, date) and not isinstance(raw_value, datetime):
                return raw_value
            if isinstance(raw_value, str):
                # Accept full datetime strings, but reduce to date()
                dt = _parse_iso_datetime(raw_value)
                return dt.date()

        if isinstance(field, (models.IntegerField, models.BigIntegerField, models.AutoField)):
            return int(raw_value)

        if isinstance(field, (models.FloatField,)):
            return float(raw_value)

        if isinstance(field, (models.DecimalField,)):
            return Decimal(str(raw_value))

        if isinstance(field, (models.BooleanField,)):
            return to_bool(raw_value)

        if isinstance(field, (models.UUIDField,)):
            return uuid.UUID(str(raw_value))

        # CharField/TextField: leave as str
        # ForeignKeys: Django accepts pk-type (int/uuid/str), leave as-is or try int
    except Exception:
        # If coercion fails, fall back to raw value (avoid crashing)
        return raw_value

    return raw_value
