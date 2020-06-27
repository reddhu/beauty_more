from django.urls import path
from . import views

urlpatterns = [path('areas/', views.ProvinceListView.as_view()),
               path('areas/<int:pk>/', views.SubAreaView.as_view())

]