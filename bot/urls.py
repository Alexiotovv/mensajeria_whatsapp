from django.urls import path,include, re_path
# from . import views
from .views import *

urlpatterns = [  
    re_path('api/v1/login',login),
    re_path('api/v1/register',register),
    re_path('api/v1/profile',profile),
    re_path("api/v1/whatsapp/", whatsapp, name="whatsapp"),

    # re_path('api/v1/list/justificaciones',views.list_justificaciones),
    path('api/v1/list/justificaciones/', ListarJustificaciones.as_view(), name='app_list_justificaciones'),

    re_path('api/v1/delete/justificaciones/<justificacion_id>',delete_justificacion),

]
