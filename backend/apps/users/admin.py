from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'full_name', 'target_exam', 'is_premium', 'created_at')
    list_filter = ('is_premium', 'target_exam', 'is_staff', 'is_superuser')
    search_fields = ('email', 'username', 'full_name')
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile Information', {
            'fields': ('full_name', 'phone', 'target_exam', 'exam_date', 'study_hours_per_day')
        }),
        ('Subscription', {
            'fields': ('is_premium', 'subscription_end_date')
        }),
        ('Activity', {
            'fields': ('last_activity',)
        }),
    )
class CustomUserAdmin(UserAdmin):

    model = User

    list_display = (
        "email",
        "username",
        "is_active",
        "is_staff",
        "is_superuser",
    )

    fieldsets = UserAdmin.fieldsets + (
        ("Extra Info", {
            "fields": (
                "full_name",
                "phone",
                "target_exam",
                "exam_date",
                "study_hours_per_day",
                "is_premium",
                "subscription_end_date",
            )
        }),
    )