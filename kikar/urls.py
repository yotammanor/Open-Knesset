
from django.conf.urls import url, patterns


from kikar import views
urlpatterns = patterns('',
                       url(r'^get-statuses/$', views.get_statuses, name='get-statuses'),
                       url(r'^get-member/(?P<pk>\d+)/$', views.get_member, name='get-member'),
)
