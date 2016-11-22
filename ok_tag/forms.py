from django import forms
from django.forms import HiddenInput
from django.utils.translation import ugettext_lazy as _
from tagging.forms import TagField

from auxiliary.models import TagSuggestion
from suggestions.forms import InstanceCreateSuggestionForm


class TagForm(forms.Form):
    tags = TagField()


class TagSuggestionForm(InstanceCreateSuggestionForm):
    name = forms.CharField(label=_('Name'))
    app_label = forms.CharField(widget=HiddenInput)
    object_type = forms.CharField(widget=HiddenInput)
    object_id = forms.CharField(widget=HiddenInput)

    class Meta:
        model = TagSuggestion
        caption = _('Suggest Tag')

    def __init__(self, *args, **kwargs):
        super(TagSuggestionForm, self).__init__(*args, **kwargs)
        self.helper.form_action = 'suggest-tag-post'

    def get_data(self, request):
        data = super(TagSuggestionForm, self).get_data(request)
        data['suggested_by'] = request.user
        return data
