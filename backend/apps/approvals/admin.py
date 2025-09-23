from django.contrib import admin

from backend.apps.approvals.models import Approval


# Register your models here.
@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    pass
