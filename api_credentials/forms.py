from django import forms
from .models import ServiceCredential

class ServiceCredentialForm(forms.ModelForm):
    client_secret = forms.CharField(widget=forms.PasswordInput, required=False, help_text='Enter the client secret here.')

    class Meta:
        model = ServiceCredential
        fields = ('name', 'tenant_id', 'client_id', 'client_secret')

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk and ServiceCredential.objects.exists():
            raise forms.ValidationError("Only one service principal is allowed.")
        return cleaned_data

    def clean_client_secret(self):
        secret = self.cleaned_data.get('client_secret')
        if secret:
            return secret
        return None

    def save(self, commit=True):
        instance = super().save(commit=False)
        secret = self.cleaned_data.get('client_secret')
        if secret:
            instance.client_secret = secret
        if commit:
            instance.save()
        return instance