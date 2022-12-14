"""Parleyit URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views

urlpatterns = [
    path('perform_transaction/', views.perform_transaction, name="perform-transaction"),
    path('download_report/', views.download_report, name="download-report"),
    path('perform_advance/', views.perform_advance, name="perform-advance"),
    path('register/', views.register, name="register"),
    path('get-details/', views.get_user_details, name="get-user-details"),
]
