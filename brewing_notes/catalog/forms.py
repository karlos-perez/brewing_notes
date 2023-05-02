from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import Malt, Fermentable, Hops, Yeasts, Misc, BeerStyle, WaterProfile, DEFAULT_GUIDES


class AbstractAddForm(forms.ModelForm):

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
        if self.fields.get('styles'):
            self.fields['styles'].widget.attrs['class'] = ''
        self.fields['description'].widget.attrs['rows'] = 12
        if self.fields.get('its_dry'):
            self.fields['its_dry'].widget.attrs['class'] = ''

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            return name
        raise forms.ValidationError(_("The name must not be empty"), code='invalid')


class MaltAddForm(AbstractAddForm):
    styles = forms.ModelMultipleChoiceField(queryset=BeerStyle.objects.filter(guides=DEFAULT_GUIDES).order_by('name'),
                                            widget=forms.CheckboxSelectMultiple,
                                            required=False)

    class Meta:
        model = Malt
        fields = ['type', 'name', 'company', 'country', 'extractivity', 'category',
                  'protein', 'color', 'share', 'description', 'styles', 'url_source']

    def clean_share(self):
        """
        Verify that the share in percent
        """
        share = int(self.cleaned_data.get("share"))
        if 0 < share < 101:
            return share
        else:
            raise forms.ValidationError(_("Share is not a percentage (0...100%)"), code='invalid')


class FermAddForm(AbstractAddForm):
    class Meta:
        model = Fermentable
        fields = ['type', 'name', 'company', 'country', 'extractivity', 'color', 'description', 'url_source']


class HopsAddForm(AbstractAddForm):
    styles = forms.ModelMultipleChoiceField(queryset=BeerStyle.objects.filter(guides=DEFAULT_GUIDES).order_by('name'),
                                            widget=forms.CheckboxSelectMultiple,
                                            required=False)

    class Meta:
        model = Hops
        fields = ['type', 'name', 'company', 'country', 'alfa_acid', 'description', 'styles', 'url_source']


class YeastsAddForm(AbstractAddForm):
    styles = forms.ModelMultipleChoiceField(queryset=BeerStyle.objects.filter(guides=DEFAULT_GUIDES).order_by('name'),
                                            widget=forms.CheckboxSelectMultiple,
                                            required=False)

    class Meta:
        model = Yeasts
        fields = ['type', 'name', 'short_name', 'company', 'country', 'tolerance',
                  'flocculation', 'attenuation', 'min_temperature', 'max_temperature',
                  'its_dry', 'description', 'styles', 'url_source']


class MiscAddForm(AbstractAddForm):
    class Meta:
        model = Misc
        fields = ['type', 'name', 'company', 'country', 'description', 'url_source']


class WaterAddForm(AbstractAddForm):
    styles = forms.ModelMultipleChoiceField(queryset=BeerStyle.objects.filter(guides=DEFAULT_GUIDES).order_by('name'),
                                            widget=forms.CheckboxSelectMultiple,
                                            required=False)
    class Meta:
        model = WaterProfile
        fields = ['name', 'description', 'calcum', 'bicarbonate', 'sulfate',
                  'chloride', 'sodium', 'magnesium', 'ph', 'styles']


class StyleAddForm(forms.ModelForm):

    class Meta:
        model = BeerStyle
        fields = ['guides', 'type', 'category', 'index', 'name',
                  'description', 'aroma', 'appearance', 'flavor', 'mouthfeel',
                  'comments', 'history', 'ingredients', 'comparison',
                  'OG_min', 'OG_max', 'FG_min', 'FG_max', 'ABV_min', 'ABV_max',
                  'IBUs_min', 'IBUs_max', 'SRM_min', 'SRM_max', 'CO2_min', 'CO2_max']


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            return name
        raise forms.ValidationError(_("The name must not be empty"), code='invalid')
