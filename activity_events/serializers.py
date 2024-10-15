from rest_framework import serializers
from .models import ActivityEvent

class ActivityEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityEvent
        fields = '__all__'