
from allauth.account.forms import SignupForm
from django import forms
from django_recaptcha.fields import ReCaptchaField
from django.contrib.auth.forms import AuthenticationForm




class AdminEmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'autofocus': True})
    )






class CustomSignupForm(SignupForm):
    email = forms.EmailField(required=True, label="Email")
    password1 = forms.CharField(
        widget=forms.PasswordInput, required=True, label="Password"
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput, required=True, label="Confirm Password"
    )
    captcha = ReCaptchaField()

    def save(self, request):
        user = super().save(request)
        # role is already default "customer", but you can enforce it here
        user.role = "customer"
        user.save()
        return user







class CustomPasswordResetForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Email', 'class': 'form-control'})
    )

