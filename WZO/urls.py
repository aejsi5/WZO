"""WZO URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from WZO_App import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('welcome/', views.welcome_view, name="Welcome"),
    path('activate/<uidb64>/<token>/', views.activate, name="Activate"),
    path('logout/', views.logout_view, name="Logout"),
    path('register/', views.Registration.as_view(), name="Register"),
    path('login/', views.Login.as_view(), name="Login"),
    path('reset/', views.Reset.as_view(), name="Reset"),
    path('reset/password/<uidb64>/<token>/', views.PasswordReset.as_view(), name="Reset-Password"),
    path('', views.index, name="Index"),
    path('settings/', views.Settings.as_view(), name="Settings"),
    path('calculate/', views.Calculate.as_view(), name="Calculate"),
    path('export/', views.Export.as_view(), name="Export"),
    path('run/<ruletype>', views.run_Rules, name="Run Rules"),
    path('import/', views.Import.as_view(), name="Importer"),
    path('api/v1/account/<pk>', views.WZOUser_Api.as_view()),
    path('api/v1/eort/<pk>', views.Eort_Api.as_view()),
    path('api/v1/eortlist/', views.Eort_List_Api.as_view()),
    path('api/v1/eort/<pk>/vehicles/', views.EortVehicleList_Api.as_view()),
    path('api/v1/vehicle/<pk>', views.Vehicle_Api.as_view()),
    path('api/v1/vehicle/<pk>/workshops/', views.VehicleWorkshopList_Api.as_view()),
    path('api/v1/rules/wear-and-tear/', views.WTRulesList_Api.as_view())
]
