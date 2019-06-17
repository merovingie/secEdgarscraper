from django.contrib import admin, auth
from django.contrib.auth import views as auth_views
from django.urls import path
from list import views
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name = 'home'),
    #auth
    path('signup', views.SignUp.as_view(), name = 'signup'),
    path('login', auth_views.LoginView.as_view(), name = 'login'),
    path('logout', auth_views.LogoutView.as_view(), name = 'logout'),
    #listings
    path('listing/create', views.Createlisting.as_view(), name = 'create_listing'),
    path('listing/<int:pk>', views.Detaillisting.as_view(), name = 'detail_listing'),

]
urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)
