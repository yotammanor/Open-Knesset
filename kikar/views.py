from django.http.response import HttpResponse
import requests


def get_statuses(request):
    url = request.GET.get('path', 'http://www.kikar.org/api/v1/facebook_status/?limit=5')
    url = url.replace("'", "").replace('"', "")
    print(url)
    kikar_res = requests.get(url)
    res = HttpResponse(content=kikar_res.content, content_type='application/json')
    return res
