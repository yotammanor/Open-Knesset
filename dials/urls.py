# encoding: UTF-8
from django.conf.urls import url, patterns
from djangoratings.views import AddRatingFromModel
from views import dial_svg, dial_html

dialsurlpatterns = patterns('',
    url(r'^dial/(?P<slug>[\w\-\"]+).svg$', dial_svg, name="dial-svg"),
    url(r'^dial/(?P<slug>[\w\-\"]+).html$', dial_html, name="dial-html"),
)
