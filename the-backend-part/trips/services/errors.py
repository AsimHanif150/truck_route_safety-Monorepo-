class TripPlanningError(Exception):
    """A problem the API user should see. `status` is the HTTP status to return."""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status
