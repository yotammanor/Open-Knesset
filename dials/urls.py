# encoding: UTF-8
from django.conf.urls import url, patterns
from djangoratings.views import AddRatingFromModel
from views import dial_svg, dial_desc

dialsurlpatterns = patterns('',
    url(r'^dial/(?P<slug>[\w\-\"]+)$', dial_svg, name="dial-svg"),
    url(r'^dial/(?P<slug>[\w\-\"]+)/desc$', dial_desc, name="dial-desc"),
)
