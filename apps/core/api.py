"""Shared API helpers (Phase 6, Sprint 6.4 - API Security and Validation).

Provides two pieces the REST API needs to be consistent and hardened:

- ``paginated_payload``: a non-breaking page-based paginator for the
  collection endpoints. Every page keeps the established ``success/message``
  keys and holds the current page's records in ``data`` while adding ``count``,
  ``page``, ``pages``, ``next`` and ``previous`` metadata (the same envelope
  the apartment search already uses). Small result sets (fewer items than
  ``page_size``) still fit entirely on page 1, so existing consumers that read
  ``data`` as a flat list keep working (§24, AGENTS 21).

- ``api_exception_handler``: a DRF ``EXCEPTION_HANDLER`` that wraps every
  exception DRF normally emits (authentication 401, permission 403, not-found
  404, method-not-allowed 405, throttling 429 and validation/parse 400) into
  the same ``success/message/data-or-errors`` envelope the hand-written views
  already use, so error responses are consistent across the whole API.
"""
from rest_framework import exceptions
from rest_framework.views import exception_handler as _drf_exception_handler

DEFAULT_PAGE_SIZE = 12


def paginated_payload(request, queryset, serializer_class, message, page_size=DEFAULT_PAGE_SIZE):
    """Return a paginated ``{success, message, count, page, pages, next,
    previous, data}`` payload for ``queryset``.

    ``data`` holds the current page's items serialized with
    ``serializer_class``. An out-of-range (or blank) ``page`` is clamped.
    """
    try:
        page = int(request.query_params.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    page = max(page, 1)

    total = queryset.count()
    pages = (total + page_size - 1) // page_size
    # Clamp an out-of-range page (e.g. ``page=999``) to the last available
    # page so consumers never receive an accidentally blank page.
    page = min(page, max(pages, 1))
    start = (page - 1) * page_size
    items = queryset[start : start + page_size]

    base = request.build_absolute_uri().split("?")[0]
    querystring = request.query_params.copy()
    querystring.pop("page", None)

    def page_link(number):
        if number is None:
            return None
        params = querystring.copy()
        if number != 1:
            params["page"] = str(number)
        query = params.urlencode()
        return f"{base}?{query}" if query else base

    return {
        "success": True,
        "message": message,
        "count": total,
        "page": page,
        "pages": pages,
        "next": page_link(page + 1 if page < pages else None),
        "previous": page_link(page - 1 if page > 1 else None),
        "data": serializer_class(items, many=True).data,
    }


def api_exception_handler(exc, context):
    """Wrap DRF exceptions into the ``success/message/errors`` envelope.

    Unhandled exceptions return ``None`` so DRF re-raises them and Django's
    error pipeline logs them without ever exposing internals (AGENTS 22).
    """
    response = _drf_exception_handler(exc, context)
    if response is None:
        return None

    message = "An error occurred."
    errors = response.data

    if isinstance(exc, exceptions.Throttled):
        message = "Too many requests. Please slow down and try again."
        errors = {
            "detail": "Request was throttled.",
            "retry_after": getattr(exc, "wait", None),
        }
    elif isinstance(exc, exceptions.NotAuthenticated):
        message = "Authentication credentials were not provided."
    elif isinstance(exc, exceptions.AuthenticationFailed):
        message = "Authentication failed."
    elif isinstance(exc, exceptions.PermissionDenied):
        message = "You do not have permission to perform this action."
    elif isinstance(exc, exceptions.NotFound):
        message = "The requested resource was not found."
    elif isinstance(exc, exceptions.MethodNotAllowed):
        message = "Method not allowed."
    elif isinstance(exc, (exceptions.ParseError, exceptions.ValidationError)):
        message = "The request could not be processed due to invalid input."

    response.data = {"success": False, "message": message, "errors": errors}
    return response
