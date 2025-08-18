from allauth.account.adapter import DefaultAccountAdapter
from django.shortcuts import resolve_url

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        # Check session for pending cart
        pending_slug = request.session.pop('pending_cart_add', None)
        if pending_slug:
            return resolve_url('cart:add', plan_slug=pending_slug)

        # Default redirect
        return resolve_url('shop:index')
