from django.db import models
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver
from django.core.files.uploadedfile import InMemoryUploadedFile

from PIL import Image
from io import BytesIO
import base64
import os

# Create your models here.

class Category(models.Model):
    id = models.AutoField(primary_key=True)
    Категорія = models.CharField(max_length=200, unique=True)

    def __str__(self) -> str:
        return self.Категорія
    

class Brand(models.Model):
    id = models.AutoField(primary_key=True)
    Бренд = models.CharField(max_length=200, unique=True)
    
    def __str__(self) -> str:
        return self.Бренд




def convert_photo(path: str, obj):
    try:
        with open(path, 'rb') as f:
            encoded =  base64.b64encode(f.read()).decode('UTF-8')
        return encoded
    except FileNotFoundError:
        return obj



class Product(models.Model):
    id = models.AutoField(primary_key=True)

    tit = models.ImageField(upload_to='static/images/',
                            blank=False, null=False)
    stit = models.ImageField(upload_to='static/images/',
                             blank=True, null=True)
    static1 = models.ImageField(upload_to='static/images/',
                             blank=True, null=True)
    static2 = models.ImageField(upload_to='static/images/',
                             blank=True, null=True)


    first = models.TextField(null=True, blank=True)
    second = models.TextField(null=True, blank=True)
    third = models.TextField(null=True, blank=True)
    fourth = models.TextField(null=True, blank=True)


    Категорія = models.ForeignKey(Category, on_delete=models.CASCADE)
    Бренд = models.ForeignKey(Brand, on_delete=models.CASCADE)
    Модель = models.CharField(null=False, max_length=200)
    Колір = models.CharField(null=False, max_length=200)
    Ціна = models.IntegerField(null=False, blank=False)
    Ціна2 = models.IntegerField(null=False, blank=False)
    Розмір = models.TextField(null=False)
    Кількість = models.IntegerField(null=False)
    Опис = models.TextField(null=True, blank=True)
    Знижка = models.IntegerField(default=0)
    data = models.DateTimeField(auto_now_add=True)

    def resize_image(self, image, width: int, height: int):
        img = Image.open(BytesIO(image))

        w, h = img.size

        ratio = min(width / w, height / h)


        resized_img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

        buffer = BytesIO()
        try:
            resized_img.save(buffer, "JPEG")
        except:
            new = resized_img.convert("RGB")
            new.save(buffer, "JPEG")

        return base64.b64encode(buffer.getvalue()).decode()

    def edit_img(self, image):
        with BytesIO() as output:
            [output.write(i) for i in image.chunks()]
            
            image.delete(False)
            return self.resize_image(output.getvalue(), 800, 800)


    def save(self, *args, **kwargs):
        self.first = self.edit_img(self.tit) if self.tit else None
        self.second = self.edit_img(self.stit) if self.stit else None
        self.third = self.edit_img(self.static1) if self.static1 else None
        self.fourth = self.edit_img(self.static2) if self.static2 else None

        super().save()


    def __str__(self):
        return f'{self.id} | {self.Категорія} | {self.Бренд} | {self.Модель} | {self.Колір}'
    

@receiver([post_delete, pre_delete], sender=Product)
def delete_image(sender, instance, **kwargs):
    print('ok')
    print(instance)



class Order(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    size = models.CharField(blank=False, max_length=200, null=False)
    name = models.CharField(blank=False, max_length=200, null=False)
    second_name = models.CharField(blank=False, max_length=200, null=False)
    phone = models.CharField(blank=False, max_length=200, null=False)
    email = models.EmailField(blank=False, null=False, unique=False)
    city = models.CharField(blank=False, max_length=200, null=False)
    warhouse = models.TextField(blank=False, null=False)
    pay = models.TextField(blank=False, null=False)
    date = models.DateTimeField(auto_now_add=True)
    count = models.IntegerField(blank=False, null=False,
                                default=1)
    done = models.BooleanField(default=0, blank=False, null=False)

    def __str__(self):
        return f"Товар id: {self.product.id} Покупець: {self.name} {self.email} {self.phone}"
    

class Pay(models.Model):
    id = models.AutoField(primary_key=True)
    method = models.CharField(unique=True, null=False, blank=False,
                              max_length=200)
    
    def __str__(self) -> str:
        return self.method
    

class BannerImage(models.Model):
    id = models.AutoField(primary_key=True)
    photo = models.ImageField(upload_to='banner/',
                              null=False, blank=False)
    
    banner = models.TextField(null=True, blank=True)

    link = models.TextField(null=True, blank=True)


    def save(self, *args, **kwargs):
        super().save()

        self.banner = convert_photo(self.photo.path, self.banner)

        super().save()

        try:
            os.remove(self.photo.path)
        except FileNotFoundError:
            pass


    def __str__(self):
        return self.photo.name

@receiver(post_delete, sender=BannerImage)
def delete_image(sender, instance, **kwargs):
    if instance.photo:
        if os.path.isfile(instance.photo.path):
            os.remove(instance.photo.path)
    
