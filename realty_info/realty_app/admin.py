from django.contrib import admin
from .models import Flats, Photos


@admin.register(Flats)
class FlatsAdmin(admin.ModelAdmin):
    list_display = ('id', 'link', 'reference', 'price', 'square', 'city', 'street', 'rooms_number', 'date',
                    'is_tg_posted', 'is_archive')
    list_filter = ('reference', 'city', 'rooms_number', 'date', 'is_tg_posted', 'is_archive')


@admin.register(Photos)
class PhotosAdmin(admin.ModelAdmin):
    list_display = ('id', 'flat', 'link')
    list_filter = ('flat',)
