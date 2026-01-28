from typing import Any, Dict, List, Optional

from django.db.models import QuerySet


def apply_sorting(queryset: QuerySet, sort_descriptors: Any) -> QuerySet:
    """
    Apply multi-column sorting. Each descriptor can be:
      { "name": "field", "direction": "ascending|descending" }
      or { "field": "field", "direction": "ascending|descending" }
    """
    if not isinstance(sort_descriptors, list) or not sort_descriptors:
        return queryset

    order_by_fields: List[str] = []
    for sort_descriptor in sort_descriptors:
        if not isinstance(sort_descriptor, dict):
            continue
        sort_field_name: Optional[str] = sort_descriptor.get('name') or sort_descriptor.get('field')
        sort_direction: str = (sort_descriptor.get('direction') or 'ascending').strip().lower()
        if sort_field_name:
            prefix = '-' if sort_direction == 'descending' else ''
            order_by_fields.append(prefix + sort_field_name)

    return queryset.order_by(*order_by_fields) if order_by_fields else queryset
