
# services/datamanager/filters.py
from typing import Any, Dict, List, Optional, Type

from django.db import models
from django.db.models import Q

from .parsing import json_or_value, normalize_operator, to_bool, coerce_value_for_field


def _string_lookup_suffix(kind: str, ignore_case: bool, value: Any) -> str:
    if kind == 'exact':
        return '__iexact' if (ignore_case and isinstance(value, str)) else '__exact'
    if kind == 'contains':
        return '__icontains' if ignore_case else '__contains'
    if kind == 'startswith':
        return '__istartswith' if ignore_case else '__startswith'
    if kind == 'endswith':
        return '__iendswith' if ignore_case else '__endswith'
    return ''


def _is_string_field(model: Type[models.Model], field_name: str) -> bool:
    try:
        field = model._meta.get_field(field_name)
    except Exception:
        return False
    return isinstance(field, (models.CharField, models.TextField))


def _like_to_q(field_name: str, pattern: Any, ignore_case: bool) -> Q:
    """
    Basic LIKE semantics using % wildcards (no _ handling).
    - '%abc%'  -> contains 'abc'
    - 'abc%'   -> startswith 'abc'
    - '%abc'   -> endswith 'abc'
    - 'abc'    -> exact
    If pattern has internal % (e.g., 'a%b%c'), we collapse to 'contains' with
    the non-% fragment to avoid expensive regex; if nothing left, no-op.
    """
    if not isinstance(pattern, str):
        # Fallback: treat as exact
        return Q(**{f"{field_name}{_string_lookup_suffix('exact', ignore_case, pattern)}": pattern})

    raw = pattern
    starts_wild = raw.startswith('%')
    ends_wild = raw.endswith('%')

    # Extract middle content without surrounding %
    stripped = raw.strip('%')

    if starts_wild and ends_wild:
        # %abc%
        if stripped:
            return Q(**{f"{field_name}{_string_lookup_suffix('contains', ignore_case, stripped)}": stripped})
        return Q()  # pattern is just '%' -> no-op

    if ends_wild and not starts_wild:
        # abc%
        return Q(**{f"{field_name}{_string_lookup_suffix('startswith', ignore_case, stripped)}": stripped})

    if starts_wild and not ends_wild:
        # %abc
        return Q(**{f"{field_name}{_string_lookup_suffix('endswith', ignore_case, stripped)}": stripped})

    # No surrounding %; if there are internal % like 'a%b', reduce to a contains
    core = raw.replace('%', '')
    if core:
        return Q(**{f"{field_name}{_string_lookup_suffix('exact', ignore_case, raw)}": raw}) if '%' not in raw \
            else Q(**{f"{field_name}{_string_lookup_suffix('contains', ignore_case, core)}": core})
    return Q()


def build_q_from_leaf_predicate(model: Type[models.Model], predicate: Dict[str, Any]) -> Q:
    field_name: Optional[str] = predicate.get('field')
    operator_name: str = normalize_operator(predicate.get('operator'))
    raw_value: Any = predicate.get('value', None)
    ignore_case: bool = to_bool(predicate.get('ignoreCase'), True)

    if not field_name:
        return Q()

    # Coerce to field type (important for numbers/dates)
    coerced_value = coerce_value_for_field(model, field_name, raw_value)

    # Equality / inequality
    if operator_name == 'equal':
        return Q(**{f"{field_name}{_string_lookup_suffix('exact', ignore_case, coerced_value)}": coerced_value})
    if operator_name == 'notequal':
        return ~Q(**{f"{field_name}{_string_lookup_suffix('exact', ignore_case, coerced_value)}": coerced_value})

    # Comparisons
    if operator_name == 'gt':
        return Q(**{f"{field_name}__gt": coerced_value})
    if operator_name == 'gte':
        return Q(**{f"{field_name}__gte": coerced_value})
    if operator_name == 'lt':
        return Q(**{f"{field_name}__lt": coerced_value})
    if operator_name == 'lte':
        return Q(**{f"{field_name}__lte": coerced_value})

    # String positives
    if operator_name == 'contains':
        return Q(**{f"{field_name}{_string_lookup_suffix('contains', ignore_case, coerced_value)}": coerced_value})
    if operator_name == 'startswith':
        return Q(**{f"{field_name}{_string_lookup_suffix('startswith', ignore_case, coerced_value)}": coerced_value})
    if operator_name == 'endswith':
        return Q(**{f"{field_name}{_string_lookup_suffix('endswith', ignore_case, coerced_value)}": coerced_value})
    if operator_name == 'like':
        # Only meaningful on string fields
        if _is_string_field(model, field_name):
            return _like_to_q(field_name, coerced_value, ignore_case)
        return Q()  # no-op for non-string fields

    # String negatives
    if operator_name == 'notcontains':
        return ~Q(**{f"{field_name}{_string_lookup_suffix('contains', ignore_case, coerced_value)}": coerced_value})
    if operator_name == 'notstartswith':
        return ~Q(**{f"{field_name}{_string_lookup_suffix('startswith', ignore_case, coerced_value)}": coerced_value})
    if operator_name == 'notendswith':
        return ~Q(**{f"{field_name}{_string_lookup_suffix('endswith', ignore_case, coerced_value)}": coerced_value})

    # Collections
    if operator_name == 'in':
        values_list = coerced_value if isinstance(coerced_value, (list, tuple)) else [coerced_value]
        return Q(**{f"{field_name}__in": values_list})
    if operator_name == 'notin':
        values_list = coerced_value if isinstance(coerced_value, (list, tuple)) else [coerced_value]
        return ~Q(**{f"{field_name}__in": values_list})
    if operator_name == 'between':
        if isinstance(coerced_value, (list, tuple)) and len(coerced_value) == 2:
            return Q(**{f"{field_name}__range": (coerced_value[0], coerced_value[1])})
        return Q()

    # Null / empty
    if operator_name == 'isnull':
        return Q(**{f"{field_name}__isnull": True})
    if operator_name == 'isnotnull':
        return Q(**{f"{field_name}__isnull": False})

    if operator_name == 'isempty':
        # Only meaningful for strings; treat empty as exactly "" (not NULL)
        if _is_string_field(model, field_name):
            return Q(**{f"{field_name}": ""})
        return Q()
    if operator_name == 'isnotempty':
        # Strings: not empty and not null
        if _is_string_field(model, field_name):
            return ~Q(**{f"{field_name}": ""}) & Q(**{f"{field_name}__isnull": False})
        return Q()

    # Unknown operator -> no-op
    return Q()


def build_q_from_where(model: Type[models.Model], where_clause: Any) -> Q:
    if where_clause is None:
        return Q()

    where_clause = json_or_value(where_clause)

    if isinstance(where_clause, list):
        combined_q = Q()
        for predicate in where_clause:
            combined_q &= build_q_from_where(model, predicate)
        return combined_q

    if isinstance(where_clause, dict):
        is_complex: bool = where_clause.get('isComplex', False)
        if is_complex:
            condition: str = (where_clause.get('condition') or 'and').strip().lower()
            predicates_list: List[Dict[str, Any]] = where_clause.get('predicates') or []
            if condition == 'or':
                combined_or_q = Q()
                has_any = False
                for child_predicate in predicates_list:
                    child_q = build_q_from_where(model, child_predicate)
                    if not has_any:
                        combined_or_q = child_q
                        has_any = True
                    else:
                        combined_or_q |= child_q
                return combined_or_q
            else:
                combined_and_q = Q()
                for child_predicate in predicates_list:
                    combined_and_q &= build_q_from_where(model, child_predicate)
                return combined_and_q
        else:
            return build_q_from_leaf_predicate(model, where_clause)

    return Q()
