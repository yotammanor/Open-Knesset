from django.shortcuts import render
from django.shortcuts import get_object_or_404, render_to_response
from models import Dial

# Create your views here.
def dial_svg(request, slug):
    dial = get_object_or_404(Dial, slug=slug)
    if dial.precent < 15:
        color = "#ED1C24"
    elif dial.precent < 40:
        color = "orange" #TODO: pick a color
    else:
        color = "green" #TODO: pick a color
    return render_to_response("dials/svg.html",
            {'width': dial.precent * 746 / 100,
             'precent': dial.precent,
             'color': color,
             })


def dial_html(request, slug):
    dial = get_object_or_404(Dial, slug=slug)
    return render_to_response("dials/text.html",
            {'dial': dial})

