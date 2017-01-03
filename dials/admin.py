from django.contrib import admin
from models import Dial

# Register your models here.
class DialAdmin(admin.ModelAdmin):
    model = Dial

admin.site.register(Dial, DialAdmin)
