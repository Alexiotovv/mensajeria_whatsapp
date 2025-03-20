from django.urls import path,include, re_path
from . import views 

urlpatterns = [  
    re_path('api/v1/login',views.login),
    re_path('api/v1/register',views.register),
    re_path('api/v1/profile',views.profile),
    re_path("api/v1/whatsapp/", views.whatsapp, name="whatsapp"),

]
