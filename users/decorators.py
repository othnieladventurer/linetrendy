from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from functools import wraps
from django.conf import settings






def require_roles(allowed_roles):
    """
    Decorator to restrict access to users with specific roles.
    - Redirects unauthenticated users to LOGIN_URL.
    - Redirects authenticated users with the wrong role to '/' (or another page).
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user

            if not user.is_authenticated:
                return redirect(settings.LOGIN_URL)

            if hasattr(user, 'role') and user.role not in allowed_roles:
                return redirect('/')  
            
            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator



    
    