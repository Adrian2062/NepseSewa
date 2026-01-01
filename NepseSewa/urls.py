from django.contrib import admin
from django.urls import path, include
from myapp import views


urlpatterns = [
    path('', include('myapp.urls')),   # Moved before admin.site.urls to prioritize custom admin routes
    path('admin/', admin.site.urls),
    path('login/', views.login_view, name='login'),
    path('accounts/', include('allauth.urls')),

]
