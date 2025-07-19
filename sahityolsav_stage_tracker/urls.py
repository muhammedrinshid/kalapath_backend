from django.urls import path, include
from sahityo_core.views import CustomTokenObtainPairView,DebugTokenRefreshView
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('sahityo_core.urls')),
    path('public-api/', include('sahityo_core.public_urls')),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', DebugTokenRefreshView.as_view(), name='token_refresh'),
]
