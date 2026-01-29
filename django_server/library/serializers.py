
from rest_framework import serializers
from .models import BookLending

class BookLendingSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookLending
        fields = "__all__"
