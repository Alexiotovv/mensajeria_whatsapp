from django.urls import path,include, re_path
from . import views

urlpatterns = [  
    re_path('api/v1/login',views.login),
    re_path('api/v1/register',views.register),
    re_path('api/v1/profile',views.profile),
    re_path("api/v1/whatsapp/", views.whatsapp, name="whatsapp"),

    # re_path('api/v1/list/justificaciones',views.list_justificaciones),
    path('api/v1/list/justificaciones/', views.ListarJustificaciones, name='list_justificaciones'),

    re_path('api/v1/delete/justificaciones/<justificacion_id>',views.delete_justificacion),

]
