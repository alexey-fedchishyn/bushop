from django.shortcuts import redirect
from django.urls import path
from django.conf.urls.static import static
from django.conf import settings

from . import views

urlpatterns = [
    path('', lambda r: redirect('/home')),
    path('home', views.search, name='home'),
    path('home/product', views.product),
    path('home/info', views.info),
    path('order', views.order),
    path('get', views.get_orders),
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)