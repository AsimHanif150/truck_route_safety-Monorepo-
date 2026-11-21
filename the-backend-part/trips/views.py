from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import TripRequestSerializer
from .services.errors import TripPlanningError
from .services.planner import plan_trip as build_plan


def _first_error(errors):
    """Flatten DRF's {field: [messages]} into one readable sentence."""
    field, messages = next(iter(errors.items()))
    return f'{field.replace("_", " ").capitalize()}: {messages[0]}'


@api_view(['POST'])
def plan_trip(request):
    """POST /api/trips/plan/ -> three weather-scored routes and a recommendation."""
    serializer = TripRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'error': _first_error(serializer.errors)}, status=400)

    data = serializer.validated_data
    try:
        plan = build_plan(
            origin_text=data['origin'],
            destination_text=data['destination'],
            departure=data['departure'],
            load_lb=data['load_weight'],
            interval_miles=int(data['checkpoint_interval']),
        )
    except TripPlanningError as error:
        return Response({'error': error.message}, status=error.status)
    return Response(plan)
