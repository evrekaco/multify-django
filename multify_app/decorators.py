from functools import wraps
from django.conf import settings
from django.http import HttpResponseRedirect


def require_https(view):
    """A view decorator that redirects to HTTPS if this view is requested
    over HTTP. Allows HTTP when DEBUG is on and during unit tests.

    """

    @wraps(view)
    def view_or_redirect(request, *args, **kwargs):
        if not request.is_secure():
            # Just load the view on a devserver or in the testing environment.
            if settings.DEBUG or request.META['SERVER_NAME'] == "testserver":
                return view(request, *args, **kwargs)

            else:
                # Redirect to HTTPS.
                request_url = request.build_absolute_uri(request.get_full_path())
                secure_url = request_url.replace('http://', 'https://')
                return HttpResponseRedirect(secure_url)

        else:
            # It's HTTPS, so load the view.
            return view(request, *args, **kwargs)

    return view_or_redirect