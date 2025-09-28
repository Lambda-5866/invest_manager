"""
URL configuration for invest_manager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from investments import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.dashboard_view, name="dashboard"),  # 대시보드
    path("api/assets/", views.asset_list, name="asset-list"),
    path("api/assets/add/", views.add_asset, name="add-asset"),
    path("api/assets/<int:pk>/delete/", views.delete_asset, name="delete-asset"),
]
