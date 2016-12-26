from django.shortcuts import render
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from models import Dial

# Create your views here.
def dial_svg(request, slug):
    dial = get_object_or_404(Dial, slug=slug)
    if dial.precent < 15:
        color = "#ED1C24" # red
    elif dial.precent < 60:
        color = "#F7AA1E" # orange
    else:
        color = "#509E33" # green
    return render_to_response("dials/dial.html",
            {'width': dial.precent * 746 / 100,
             'precent': dial.precent,
             'color': color,
             'slug': dial.slug,
             },
            context_instance=RequestContext(request))


def dial_desc(request, slug):
    dial = get_object_or_404(Dial, slug=slug)
    return render_to_response("dials/desc.html",
            {'dial': dial},
            context_instance=RequestContext(request))

