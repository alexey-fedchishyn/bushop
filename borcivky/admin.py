from django.contrib import admin
from django.utils.html import format_html

from .models import (Product, 
                     Order, Pay,
                     BannerImage, Category,
                     Brand)

# Register your models here.

class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'image', 'Категорія', 'Бренд', 'Модель']

    def image(self, obj):
        elems = [obj.first, obj.second, obj.third, obj.fourth]

        string = ''
        for i in [j for j in elems if j]:
            string += f"<img src='data:image/jpeg;base64,{i}' width='100' />\n"

        return format_html(string)
    
class BannerAdmin(admin.ModelAdmin):
    list_display = ['id', 'image', 'link']

    def image(self, obj):
        return format_html(f"<img src='data:image/jpeg;base64,{obj.banner.tobytes().decode('UTF-8')}' width='400' />")

admin.site.register(Product, ProductAdmin)
admin.site.register(BannerImage, BannerAdmin)
admin.site.register([Order, Pay, Category, Brand])