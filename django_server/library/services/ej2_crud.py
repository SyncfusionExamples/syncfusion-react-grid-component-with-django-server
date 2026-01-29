from typing import Optional

from django.db import transaction
from rest_framework import status
from rest_framework.response import Response


def _handle_insert(viewset, payload) -> Response:
    record_data = payload.get('value') or payload
    serializer = viewset.get_serializer(data=record_data)
    serializer.is_valid(raise_exception=True)
    with transaction.atomic():
        viewset.perform_create(serializer)
        instance = serializer.instance
        if instance is not None:
            instance.refresh_from_db()
        output_data = viewset.get_serializer(instance).data
    return Response(output_data, status=status.HTTP_201_CREATED)


def _handle_update(viewset, payload) -> Response:
    record_id = payload.get('key') or payload.get('id') or payload.get('record_id')
    record_data = payload.get('value') or payload
    if record_id is None:
        return Response({'detail': 'Missing key for update.'}, status=status.HTTP_400_BAD_REQUEST)
    instance = viewset.get_queryset().filter(pk=record_id).first()
    if not instance:
        return Response({'detail': f'Record {record_id} not found.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = viewset.get_serializer(instance, data=record_data, partial=False)
    serializer.is_valid(raise_exception=True)
    with transaction.atomic():
        viewset.perform_update(serializer)
        instance.refresh_from_db()
        output_data = viewset.get_serializer(instance).data
    return Response(output_data, status=status.HTTP_200_OK)


def _handle_remove(viewset, payload) -> Response:
    record_id = payload.get('key') or payload.get('id') or payload.get('record_id')
    if record_id is None:
        return Response({'detail': 'Missing key for delete.'}, status=status.HTTP_400_BAD_REQUEST)
    instance = viewset.get_queryset().filter(pk=record_id).first()
    if not instance:
        return Response({'detail': f'Record {record_id} not found.'}, status=status.HTTP_404_NOT_FOUND)
    deleted_payload = viewset.get_serializer(instance).data
    with transaction.atomic():
        viewset.perform_destroy(instance)
    return Response(deleted_payload, status=status.HTTP_200_OK)


def handle_crud_action(viewset, payload) -> Optional[Response]:
    """
    Dispatch UrlAdaptor CRUD by 'action' key.
    Returns a DRF Response when handled, otherwise None.
    """
    action = payload.get('action')
    if action == 'insert':
        return _handle_insert(viewset, payload)
    if action == 'update':
        return _handle_update(viewset, payload)
    if action == 'remove':
        return _handle_remove(viewset, payload)
    return None
