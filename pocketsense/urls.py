"""
URL configuration for pocketsense project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from core.views import (
    StudentViewSet,
    GroupViewSet,
    ExpenseViewSet,
    SettlementViewSet,
    CategoryViewSet,
    MonthlyAnalysisViewSet,

)


schema_view = get_schema_view(
    openapi.Info(
        title="PocketSense API",
        default_version='v1',
        description="API documentation for PocketSense",
    ),
    public=True,
)

# Define API routes using DefaultRouter
router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='students')
router.register(r'groups', GroupViewSet, basename='groups')
router.register(r'expenses', ExpenseViewSet, basename='expenses')
router.register(r'settlements', SettlementViewSet, basename='settlements')
router.register(r'categories', CategoryViewSet, basename='categories')

# URL patterns
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),  # Include all router-registered routes
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'), # Swagger docs

    # Custom URLs for additional functionality
    #path('expenses/', ExpenseViewSet.as_view({'post': 'create'}), name='expense-create'),  # Create expense
    #path('groups/', GroupViewSet.as_view({'post': 'create'}), name='group-create'),  # Create group
    #path('settlements/', SettlementViewSet.as_view({'get': 'list'}), name='settlement-list'),  # List settlements
    path('settlements/<int:pk>/reminder/', SettlementViewSet.as_view({'post': 'reminder'}), name='settlement-reminder'),  # Payment reminder
    path('analysis/monthly/', MonthlyAnalysisViewSet.as_view({'get': 'list'}), name='monthly-analysis'),  # Monthly analysis
]
