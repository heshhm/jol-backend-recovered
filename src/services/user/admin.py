from django.contrib import admin
from .models import User, UserProfile, UserWallet

class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'created_at', 'updated_at')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'created_at', 'updated_at')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fields = ('username', 'password', 'first_name', 'last_name', 'email', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'last_login', 'date_joined', 'created_at', 'updated_at')

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'bio', 'location', 'birth_date')
    search_fields = ('user__username', 'user__email', 'location')
    list_filter = ('birth_date',)
    ordering = ('user',)

class UserWalletAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_coins', 'available_coins', 'used_coins')
    search_fields = ('user__username', 'user__email')
    list_filter = ('total_coins', 'available_coins', 'used_coins')
    ordering = ('user',)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # In edit mode
            return 'user', 'created_at', 'updated_at'
        return 'created_at', 'updated_at'

admin.site.register(User, UserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(UserWallet, UserWalletAdmin)
