from django import forms
from .models import Newsletter, Testimonial









class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Newsletter
        fields = ['email']






class TestimonialAdminForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = "__all__"
        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "Client name — e.g. Jane Doe",
                "class": "form-control",
            }),
            "content": forms.Textarea(attrs={
                "placeholder": "Write the testimonial...",
                "rows": 8,
                "class": "form-control",
            }),
            "rating": forms.NumberInput(attrs={
                "min": 0,
                "max": 5,
                "class": "form-control",
            }),
        }

        
