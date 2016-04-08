from django import forms
from tagging.forms import TagField


class TagForm(forms.Form):
    tags = TagField()