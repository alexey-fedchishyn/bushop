from typing import Any
from django.contrib import admin
from django.utils.html import format_html

from . import models as m

# Register your models here.

@admin.register(m.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display=[
        "id", "Категорія",
        "Бренд", "Модель",
        "Колір", "Ціна"
    ]


    list_filter = [
        "Категорія", "Бренд"
    ]

    search_fields = [
        "id", "Модель", "Колір"
    ]

    readonly_fields = ["image", "data"]

    list_per_page = 30

    fieldsets = (
        ("Медіа", 
            {"fields": ("image",)}
        ),
        ("Додати фото", 
            {"fields": (
                "tit",
                "stit",
                "static1",
                "static2",
            )}
        ),
        ("Дані товару",
            {"fields": (
                "Категорія", "Бренд",
                "Модель", "Колір",
                "Ціна", "Розмір",
                "Кількість", "Опис",
                "data",
            )}
        ),
    )
    
@admin.register(m.BannerImage)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['id', 'image', 'link']

    def image(self, obj):
        return format_html(f"<img src='data:image/jpeg;base64,{obj.banner}' width='400' />")


@admin.register(m.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "name","second_name", "phone",
        "email", "city",
        "warhouse", "pay",
        "date",
    ]

    list_filter = [
        "city", "pay"
    ]

    search_fields = [
        "name", "second_name", "phone",
        "email", "city", "warhouse",
    ]

    readonly_fields = (
        "name", "second_name", "phone",
        "email", "city", "warhouse", "pay",
        "date", "product", "size", "count"
    )

    

    fieldsets = (
        ("Дані користувача", 
            {"fields": (
                "name","second_name", 
                "phone", "email" 
            )}
        ),
        ("Інформація про доставку",
            {"fields": (
                "city", "warhouse"
            )}
        ),
        ("Інформація про замовлення",
            {"fields": (
                "product", "size", 
                "count", "pay",
                "date"
            )}
        ),
        ("Замовлення виконано?",
            {"fields": (
                "done",
            )}

        )
    )

admin.site.register([m.Pay, m.Category, m.Brand])