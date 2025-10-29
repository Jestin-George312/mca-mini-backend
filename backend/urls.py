"""
URL configuration for backend project.

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
# backend/urls.py
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('authen.urls')),
]

"""

"""def home_view(request):
    return render(request, 'index.html') """

from django.contrib import admin
from django.urls import path, include
from . import admin_views  # Make sure this import is here

urlpatterns = [
    # 1. Your custom admin homepage MUST come first
    path('admin/', admin_views.my_admin_index, name='admin_index'),
    
    # 2. Your other custom admin pages MUST come second
    path('admin/user-graph/', admin_views.user_graph_view, name='user_graph'),
    
    # 3. The default admin site (which includes the 404 catch-all) MUST come last
    path('admin/', admin.site.urls), 

    # --- Your API URLs ---
    path('api/auth/', include('authen.urls')),
    path('api/upload/',include('materials.urls')),
    path('topic-analysis/', include('topic_analysis.urls')), 
    path('api/timetable/', include('timetable.urls')),
    path('api/quiz/', include('quiz.urls')),
    path('api/reports/', include('reports.urls')),
]