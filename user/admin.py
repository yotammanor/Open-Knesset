from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from models import UserProfile


class UserProfileAdmin(ImportExportModelAdmin):

    pass

admin.site.register(UserProfile, UserProfileAdmin)


