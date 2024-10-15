from django.contrib import admin, messages
from .models import ServiceCredential
from .forms import ServiceCredentialForm
from .util import get_access_token
from django.urls import path, reverse
from django.http import HttpResponseRedirect


class ServiceCredentialAdmin(admin.ModelAdmin):
    form = ServiceCredentialForm
    list_display = ('name', 'tenant_id', 'client_id', 'updated_at')
    search_fields = ('name', 'tenant_id', 'client_id')
    readonly_fields = ('updated_at',)
    fieldsets = (
        (None, {
            'fields': ('name', 'tenant_id', 'client_id', 'client_secret', 'updated_at')
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('admin_check_response/<int:pk>/', self.admin_site.admin_view(self.admin_check_response), name='admin-check-response')
        ]
        return custom_urls + urls
    
    def admin_check_response(self, request, pk):
        try:
            get_access_token(pk)
            message = f'Response 200: successful service authentication!'
            level = messages.SUCCESS                     
        except Exception as e:
            message = str(e)
            level = messages.ERROR            
        finally:
            self.message_user(request, message, level=level)

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['admin_check_response_url'] = reverse('admin:admin-check-response', args=[object_id])
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('name', 'tenant_id', 'client_id')
        return self.readonly_fields    
    
    def has_add_permission(self, request):
        if ServiceCredential.objects.exists():            
            return False
        else:
            return True

admin.site.register(ServiceCredential, ServiceCredentialAdmin)
