
# views.py
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.response import Response

from .models import BookLending
from .serializers import BookLendingSerializer
from .services.datamanager.engine import DataManagerEngine
from .services.ej2_crud import handle_crud_action


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

    dm_engine = DataManagerEngine()

    def create(self, request, *args, **kwargs):
        payload = request.data

        # 1) DataManager READ via POST (initial load / filtering / sorting / paging / search / select)
        if self.dm_engine.is_dm_read(payload):
            mode, data, total_count, requires_counts = self.dm_engine.read(self.get_queryset(), payload)

            if mode == "values":
                # select-mode returns list[dict] (already projected)
                response_payload = {'result': data, 'count': total_count} if requires_counts else data
                return Response(response_payload, status=status.HTTP_200_OK)

            # rows-mode: serialize model instances
            serialized = self.get_serializer(data, many=True).data
            response_payload = {'result': serialized, 'count': total_count} if requires_counts else serialized
            return Response(response_payload, status=status.HTTP_200_OK)

        # 2) UrlAdaptor CRUD actions via POST
        crud_response = handle_crud_action(self, payload)
        if crud_response is not None:
            return crud_response

        # 3) Fallback: standard RESTful create
        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            self.perform_create(serializer)
            instance = serializer.instance
            if instance is not None:
                instance.refresh_from_db()
            output_data = self.get_serializer(instance).data
        headers = self.get_success_headers(serializer.data)
        return Response(output_data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            self.perform_update(serializer)
            instance.refresh_from_db()
            output_data = self.get_serializer(instance).data
        return Response(output_data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        deleted_payload = self.get_serializer(instance).data  # capture before deletion
        with transaction.atomic():
            self.perform_destroy(instance)
        return Response(deleted_payload, status=status.HTTP_200_OK)
