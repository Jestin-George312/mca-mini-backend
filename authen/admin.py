# root/authen/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.db.models import Q
from datetime import timedelta

# Import your own models
from .models import UserProfile

# --- 1. Define your custom filter ---
class ActivityStatusFilter(admin.SimpleListFilter):
    """
    This is a custom filter for the admin list.
    It lets you filter users by "Active" (logged in last 30 days)
    or "Passive" (haven't).
    """
    title = 'Activity Status' # Title for the filter
    parameter_name = 'activity' # URL parameter

    def lookups(self, request, model_admin):
        """
        Returns the filter options.
        """
        return (
            ('active', 'Active (Last 30 Days)'),
            ('passive', 'Passive'),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the selected option.
        """
        thirty_days_ago = now() - timedelta(days=30)
        
        if self.value() == 'active':
            # Users who logged in since 30 days ago
            return queryset.filter(last_login__gte=thirty_days_ago)
        
        if self.value() == 'passive':
            # Users who logged in *before* 30 days ago OR never logged in
            return queryset.filter(
                Q(last_login__lt=thirty_days_ago) | Q(last_login__isnull=True)
            )

# --- 2. Create a custom User admin ---
class CustomUserAdmin(UserAdmin):
    """
    This customizes the User list page.
    """
    list_display = (
        'username', 
        'email', 
        'first_name', 
        'last_name', 
        'is_active', 
        'last_login' # Show when they last logged in
    )
    search_fields = ('username', 'email', 'first_name', 'last_name') # Add a search bar
    list_filter = (
        ActivityStatusFilter, # Use your custom filter!
        'is_active',          # Add default filters
        'is_staff', 
        'is_superuser'
    )
    ordering = ('-last_login',) # Show most recent users first

# --- 3. Register your models ---
admin.site.register(UserProfile)

# Unregister the default User admin
admin.site.unregister(User) 
# Register your custom User admin
admin.site.register(User, CustomUserAdmin)