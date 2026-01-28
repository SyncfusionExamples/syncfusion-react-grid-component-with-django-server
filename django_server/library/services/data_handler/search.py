
# services/datamanager/search.py
from typing import Any, Dict, List, Type

from django.db import models
from django.db.models import Q, QuerySet

from .parsing import json_or_value, normalize_operator, to_bool
from .filters import build_q_from_leaf_predicate


def apply_search(queryset: QuerySet, payload: Dict[str, Any]) -> QuerySet:
    search_blocks = payload.get('search')
    if not search_blocks:
        if isinstance(search_blocks, str):
            simple_term = search_blocks
            default_fields = [
                'book_title', 'isbn_number', 'author_name',
                'borrower_name', 'borrower_email'
            ]
            or_query = Q()
            for default_field in default_fields:
                or_query |= Q(**{default_field + '__icontains': simple_term})
            return queryset.filter(or_query)
        return queryset

    search_blocks = json_or_value(search_blocks)
    if isinstance(search_blocks, dict):
        search_blocks = [search_blocks]
    if not isinstance(search_blocks, list) or not search_blocks:
        return queryset

    model: Type[models.Model] = queryset.model
    combined_and_q = Q()
    for search_block in search_blocks:
        fields_in_block: List[str] = search_block.get('fields') or []
        operator_name: str = normalize_operator(search_block.get('operator') or 'contains')
        search_term: Any = search_block.get('key') or search_block.get('searchKey')
        ignore_case: bool = to_bool(search_block.get('ignoreCase'), True)

        if not fields_in_block:
            single_field = search_block.get('field')
            if single_field:
                fields_in_block = [single_field]

        if not fields_in_block or search_term is None:
            continue

        block_or_q = Q()
        for field_name in fields_in_block:
            leaf_predicate = {
                'isComplex': False,
                'field': field_name,
                'operator': operator_name,
                'value': search_term,
                'ignoreCase': ignore_case,
            }
            block_or_q |= build_q_from_leaf_predicate(model, leaf_predicate)
        combined_and_q &= block_or_q

    return queryset.filter(combined_and_q) if combined_and_q else queryset
