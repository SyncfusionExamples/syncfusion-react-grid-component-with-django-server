
# services/datamanager/engine.py
from typing import Any, Dict, Tuple, List

from django.db.models import QuerySet

from .parsing import to_bool, json_or_value
from .search import apply_search
from .filters import build_q_from_where
from .sorting import apply_sorting


class DataManagerEngine:
    """
    Single-pass DataManager engine that handles:
      - search -> where -> sorting
      - paging (skip/take)
      - optional projection via `select` (values + distinct)
    Returns a tuple describing the mode and the data:
      - ("values", list_of_dicts, total_count, requires_counts) when `select` present
      - ("rows", paged_queryset, total_count, requires_counts) otherwise
    """
    DM_READ_KEYS = {'requiresCounts', 'skip', 'take', 'sorted', 'where', 'search', 'select'}

    def is_dm_read(self, payload: Dict[str, Any]) -> bool:
        return any(key in payload for key in self.DM_READ_KEYS)

    def read(self, base_queryset: QuerySet, payload: Dict[str, Any]) -> Tuple[str, Any, int, bool]:
        """
        Unified read. Decides values-mode vs rows-mode based on `select` presence.

        Returns:
            mode: "values" | "rows"
            data: list[dict] (values mode) | QuerySet (rows mode)
            total_count: int
            requires_counts: bool
        """
        queryset = base_queryset

        # 1) Search
        queryset = apply_search(queryset, payload)

        # 2) Where (complex predicates)
        where_filters = json_or_value(payload.get('where'))
        if where_filters:
            where_q_object = build_q_from_where(queryset.model, where_filters)
            if where_q_object:
                queryset = queryset.filter(where_q_object)

        # 3) Sorting
        sort_descriptors = json_or_value(payload.get('sorted'))
        queryset = apply_sorting(queryset, sort_descriptors)

        # 4) Paging params
        try:
            skip = int(payload.get('skip', 0))
        except Exception:
            skip = 0
        try:
            take = int(payload.get('take', 12))
        except Exception:
            take = 12

        requires_counts = to_bool(payload.get('requiresCounts'), False)

        # 5) Projection (SELECT) vs rows
        select_fields = payload.get('select')
        if isinstance(select_fields, (list, tuple)) and len(select_fields) > 0:
            # Values mode
            values_qs = queryset.values(*select_fields).distinct()
            total_count = values_qs.count()
            paged_values = list(values_qs[skip: skip + take])
            return "values", paged_values, total_count, requires_counts

        # Rows mode (model instances)
        total_count = queryset.count()
        paged_queryset = queryset[skip: skip + take]
        return "rows", paged_queryset, total_count, requires_counts
