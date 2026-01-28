
# services/datamanager/select.py
from typing import Any, Dict, List, Tuple

from django.db.models import QuerySet


def apply_select(
    queryset: QuerySet,
    select_fields: List[str],
    sort_descriptors: Any,
    skip: int,
    take: int,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Projects the queryset to the specified fields and returns distinct rows.

    Processing order:
      - queryset should already have search/where applied by the engine
      - apply sort (if any) using existing engine sorting logic (already applied upstream)
      - apply projection via .values(*select_fields)
      - apply .distinct() to ensure unique combinations
      - count total distinct rows
      - apply paging (skip/take)
      - return list of dicts
    """
    # Note: Sorting is expected to be applied by the engine BEFORE select,
    # but if you prefer to sort after values(), it also works as long as
    # sort fields are a subset of select_fields (DB-dependent nuance).
    values_qs = queryset.values(*select_fields).distinct()

    total_count = values_qs.count()
    paged_values = values_qs[skip: skip + take]
    return list(paged_values), total_count
