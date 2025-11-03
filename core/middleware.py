from django.conf import settings
from django.shortcuts import redirect
from urllib.parse import quote as urlquote


class RequireLoginMiddleware:
    """
    Require authentication for all views except:
    - Public apps: project_info ('/project-info/'), tests ('/testing/'), directory ('/directory/')
      Note: '/testing/moderator/' remains protected.
    - Root ('/') landing page if present
    - Static and media files
    - Explicitly allowed paths (e.g., LOGIN_URL)
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.always_allow_prefixes = ('/static/', '/media/')
        self.public_prefixes = ('/', '/project-info/', '/testing/', '/directory/')
        self.protected_subprefixes = ('/testing/moderator/',)
        self.allowed_paths = set(filter(None, [getattr(settings, 'LOGIN_URL', None), '/admin/login/']))

    def __call__(self, request):
        path = request.path

        # Allow static/media
        if path.startswith(self.always_allow_prefixes):
            return self.get_response(request)

        # Allow explicit paths like login
        if any(path.startswith(p) for p in self.allowed_paths):
            return self.get_response(request)

        # Public areas: '/', '/project-info/', '/testing/' excluding '/testing/moderator/'
        is_public = any(path.startswith(p) for p in self.public_prefixes) and not any(
            path.startswith(p) for p in self.protected_subprefixes
        )
        if is_public:
            return self.get_response(request)

        # Else require auth
        if request.user.is_authenticated:
            return self.get_response(request)

        login_url = getattr(settings, 'LOGIN_URL', '/accounts/login/')
        next_param = urlquote(request.get_full_path())
        return redirect(f"{login_url}?next={next_param}")


