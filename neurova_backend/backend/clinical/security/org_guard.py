from .exceptions import OrgIsolationError, NotFoundInOrg

def get_request_org_id(request):
    org_id = request.headers.get("X-ORG-ID")
    if not org_id:
        raise OrgIsolationError("Missing X-ORG-ID header")
    return org_id

def require_org_match(request_org_id, object_org_id):
    if str(request_org_id) != str(object_org_id):
        raise NotFoundInOrg("Object not found in this org")
