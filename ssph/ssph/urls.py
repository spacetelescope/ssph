"""
URL configuration for ssph project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    #path('admin/', admin.site.urls),
    path("secure/ssph_admin.cgi", views.admin_page, name="admin page"),
    path("secure/ssph_auth.cgi", views.auth_page, name="auth_page"),
    path("secure/sso.cgi", views.sso_page, name="sso_page"),
    path("unsecured/ssph_confirm.cgi", views.confirm_page, name="confirm_page"),
    path("", views.index, name="index")
]
