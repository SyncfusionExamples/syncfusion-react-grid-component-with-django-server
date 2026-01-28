# views.py
from rest_framework import viewsets, status
from rest_framework.response import Response

from .models import BookLending
from .serializers import BookLendingSerializer
from .services.data_handler.engine import DataHanlerEngine
from .services.crud_handler import handle_crud_action


class BookLendingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for BookLending supporting:
      - Syncfusion EJ2 DataManager read (UrlAdaptor POST): search, where (nested), sorting, paging,
        and optional select (values + distinct).
      - UrlAdaptor CRUD via 'action': insert | update | remove.
      - Standard RESTful create/update/delete fallbacks.
    """
    queryset = BookLending.objects.all()
    serializer_class = BookLendingSerializer

    # Allow only POST on the endpoint (blocks GET/PUT/PATCH/DELETE)
    http_method_names = ["post"]

    dm_engine = DataHanlerEngine()

    def create(self, request, *args, **kwargs):
        payload = request.data

        # 1) DataManager READ via POST (initial load / filtering / sorting / paging / search / select)
        if self.dm_engine.is_dm_read(payload):
            mode, data, total_count, requires_counts = self.dm_engine.read(self.get_queryset(), payload)

            if mode == "values":
                # select-mode returns list[dict] (already projected)
                return Response(
                    {'result': data, 'count': total_count} if requires_counts else data,
                    status=status.HTTP_200_OK
                )

            # rows-mode: serialize model instances
            serialized = self.get_serializer(data, many=True).data
            return Response(
                {'result': serialized, 'count': total_count} if requires_counts else serialized,
                status=status.HTTP_200_OK
            )

        # 2) UrlAdaptor CRUD actions via POST
        crud_response = handle_crud_action(self, payload)
        if crud_response is not None:
            return crud_response

        # 3) Unsupported payload
        return Response(
            {
                "detail": (
                    "Unsupported POST payload. Expected Syncfusion DataManager read payload "
                    "or UrlAdaptor CRUD action ('insert' | 'update' | 'remove')."
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )