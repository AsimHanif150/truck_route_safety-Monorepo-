from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from .services.checkpoints import CHECKPOINT_INTERVALS

MAX_DAYS_AHEAD = 14  # Open-Meteo forecasts reach 16 days; the last days are not reliable


class TripRequestSerializer(serializers.Serializer):
    origin = serializers.CharField(max_length=200)
    destination = serializers.CharField(max_length=200)
    departure = serializers.DateTimeField()
    load_weight = serializers.IntegerField(min_value=1, max_value=200_000)
    checkpoint_interval = serializers.ChoiceField(choices=CHECKPOINT_INTERVALS, default=25)

    def validate_departure(self, value):
        now = timezone.now()
        if value < now - timedelta(hours=1):
            raise serializers.ValidationError('Departure time cannot be in the past.')
        if value > now + timedelta(days=MAX_DAYS_AHEAD):
            raise serializers.ValidationError(f'Departure must be within {MAX_DAYS_AHEAD} days.')
        return value
