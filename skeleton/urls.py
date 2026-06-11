from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from django.conf import settings


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('filesystem.urls')),
    path('schema', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
