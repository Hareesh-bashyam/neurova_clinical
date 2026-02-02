import uuid

class RequestIDMiddleware:
    """
    Adds X-Request-ID to every request/response.
    Also attaches request_id on request for logging and error capture.
    """
    HEADER = "HTTP_X_REQUEST_ID"
    RESPONSE_HEADER = "X-Request-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        rid = request.META.get(self.HEADER) or str(uuid.uuid4())
        request.id = rid                 
        request.request_id = rid         
        response = self.get_response(request)
        response[self.RESPONSE_HEADER] = rid
        return response