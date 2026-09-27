"""Platform gateway router — routes requests to backend services."""
from dataclasses import dataclass


@dataclass
class Route:
    path_prefix: str
    backend_url: str
    timeout_seconds: int = 30
    require_auth: bool = True


ROUTES: list[Route] = [
    Route(path_prefix="/api/v1/behavior", backend_url="http://api:8000", require_auth=True),
    Route(path_prefix="/api/v1/threat", backend_url="http://api:8000", require_auth=True),
    Route(path_prefix="/api/v1/response", backend_url="http://api:8000", require_auth=True),
    Route(path_prefix="/health", backend_url="http://api:8000", require_auth=False),
    Route(path_prefix="/readiness", backend_url="http://api:8000", require_auth=False),
]


def get_route(path: str) -> Route | None:
    """Find the matching route for a given request path."""
    for route in ROUTES:
        if path.startswith(route.path_prefix):
            return route
    return None
