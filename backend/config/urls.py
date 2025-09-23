from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from backend.config.views import index

handler400 = "backend.config.views.handler400"
handler403 = "backend.config.views.handler403"
handler404 = "backend.config.views.handler404"
handler500 = "backend.config.views.handler500"

urlpatterns = [
    path("", include("django_prometheus.urls")),
    path("", index),
    path("users/", include("backend.apps.users.urls")),
    path("approvals/", include("backend.apps.approvals.urls")),
]

if settings.DJANGO_ENV == "dev":
    urlpatterns += (path("admin/", admin.site.urls),)

    from django.conf.urls.static import static

    urlpatterns += static(
        prefix=settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
    urlpatterns += static(prefix=settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# if settings.DEBUG:
#     import debug_toolbar
#
#     urlpatterns += [
#         path("__debug__/", include(debug_toolbar.urls)),
#     ]
