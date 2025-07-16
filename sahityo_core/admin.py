from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from django.contrib import admin
from .models import Sector, Unit, Stage, Category, Competition, ScheduledCompetition




class CustomUserAdmin(UserAdmin):
    model = User

    # Change ordering to email
    ordering = ['email']

    # Adjust fields as per your User model
    list_display = ['email', 'role', 'is_staff', 'is_active']
    search_fields = ['email']

    # Override fieldsets if you customized them, replace username with email
    fieldsets = (
        (None, {'fields': ('email', 'password', 'role')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'is_staff', 'is_active'),
        }),
    )

admin.site.register(User, CustomUserAdmin)



@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ['name', 'user','id']
    search_fields = ['name', 'user__email']
    autocomplete_fields = ['user']

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    
    list_display = ['name', 'user']
    search_fields = ['name', 'user__email']
    autocomplete_fields = ['user']

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ['name', 'user']
    search_fields = ['name', 'user__email']
    autocomplete_fields = ['user']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    search_fields = ['name', 'category__name']
    autocomplete_fields = ['category']

@admin.register(ScheduledCompetition)
class ScheduledCompetitionAdmin(admin.ModelAdmin):
    list_display = ['competition', 'stage', 'reporting_time', 'start_time', 'end_time', 'status']
    search_fields = ['competition__name', 'stage__name']
    list_filter = ['status', 'stage__name', 'competition__category__name']
    autocomplete_fields = ['competition', 'stage']
