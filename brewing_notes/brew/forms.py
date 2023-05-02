import re

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from nnmware.core.forms import RegistrationForm
from nnmware.core.models import Message

from catalog.models import BeerStyle, DEFAULT_GUIDES

from .models import BrewUser, Recipe, MashGuidelines, GrainIngredients, FermentableIngredients, \
    HopsIngredients, MiscIngredients, YeastsIngredients, Priming, BrewingLog, \
    WaterTargetProfile, FermentationGuidelines, WaterOriginalProfile, WaterIngredient


class AbstractAddForm(forms.ModelForm):
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
        if self.fields.get('note'):
            self.fields['note'].widget.attrs['class'] = 'form-control note'


class AuthUserForm(AuthenticationForm, forms.ModelForm):
    class Meta:
        model = BrewUser
        fields = ('username', 'password')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    # def confirm_login_allowed(self, user):
    #     """
    #     Controls whether the given User may log in. This is a policy setting,
    #     independent of end-user authentication. This default behavior is to
    #     allow login by active users, and reject login by inactive users.
    #
    #     If the given user cannot log in, this method should raise a
    #     ``ValidationError``.
    #
    #     If the given user may log in, this method should return None.
    #     """
    #     if not user.is_active:
    #         raise ValidationError(
    #             self.error_messages['inactive'],
    #             code='inactive',
    #         )


class RegisterUserForm(RegistrationForm):
    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = _('Required. 16 characters or fewer.'
                                              ' Letters, digits and - _ only')
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise forms.ValidationError(_('Username is required'), code='invalid')
        if not re.match("^[A-Za-z0-9_-]*$", username):
            raise forms.ValidationError(_('Incorrect letters in username'), code='invalid')
        if len(username) < 3:
            raise forms.ValidationError(_('Minimum - 3 letters'), code='invalid', )
        if len(username) > 16:
            raise forms.ValidationError(_('Maximum - 16 letters'), code='invalid')
        user_model = get_user_model()
        try:
            user = user_model.objects.get(username__iexact=username)
            if not user.is_confirm:
                if user.emailconfirmation.expire_dt():
                    user.delete()
                    raise user_model.DoesNotExist
        except user_model.DoesNotExist:
            return username
        raise forms.ValidationError(_("This username has already existed."), code='invalid')

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not password:
            raise forms.ValidationError(_('Password is required'), code='invalid')
        return password


class ResendConfirmationForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['username', ]


class RecipeForm(AbstractAddForm):
    class Meta:
        model = Recipe
        fields = '__all__'


class RecipeAddFullForm(AbstractAddForm):
    style = forms.ModelChoiceField(queryset=BeerStyle.objects.filter(guides=DEFAULT_GUIDES))

    class Meta:
        model = Recipe
        widgets = {'description': forms.Textarea(attrs={'rows': '2'}),
                   'note': forms.Textarea(attrs={'rows': '2'}),
                   'PBG': forms.NumberInput(attrs={'placeholder': 'SG (1.xxx)'}),
                   'OG': forms.NumberInput(attrs={'placeholder': 'SG (1.xxx)'}),
                   'FG': forms.NumberInput(attrs={'placeholder': 'SG (1.xxx)'}),
                   'img': forms.FileInput(attrs={'accept': '.jpg,.jpeg'})}
        # fields = '__all__'
        exclude = ['created_date', 'karma', 'user', 'type', 'сonformity', 'status',
                   'efficiency_brew', 'fermentation_temp', 'fermentation_duration',
                   'fermentation_size']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
        self.fields['show_note'].widget.attrs['class'] = ''
        self.fields['show_log'].widget.attrs['class'] = ''

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            return name
        raise forms.ValidationError(_("The name must not be empty"), code='invalid')

    def clean_img(self):
        image = self.cleaned_data.get('img', None)
        if image:
            if image.size > settings.MAX_UPLOAD_IMAGE_SIZE:
                raise forms.ValidationError(_(f'Image file too large ( > {settings.MAX_UPLOAD_IMAGE_SIZE/1048576}MB )'))
            return image


class MashGuidelinesAddForm(AbstractAddForm):
    class Meta:
        model = MashGuidelines
        fields = '__all__'

    # def clean_step_temp(self):
    #     step_temp = self.cleaned_data.get('step_temp')
    #     if step_temp:
    #         return step_temp
    #     raise forms.ValidationError(_("Required field"), code='invalid')


class GrainIngredientsAddForm(AbstractAddForm):
    class Meta:
        model = GrainIngredients
        fields = '__all__'


class FermentableIngredientsAddForm(AbstractAddForm):
    class Meta:
        model = FermentableIngredients
        fields = '__all__'


class HopsIngredientsAddForm(AbstractAddForm):
    class Meta:
        model = HopsIngredients
        fields = '__all__'


class MiscIngredientsAddForm(AbstractAddForm):
    class Meta:
        model = MiscIngredients
        fields = '__all__'


class YeastsIngredientsAddForm(AbstractAddForm):
    class Meta:
        model = YeastsIngredients
        fields = '__all__'


class BrewingLogAddForm(AbstractAddForm):
    date = forms.DateField(input_formats=settings.DATE_INPUT_FORMATS, required=False)

    class Meta:
        model = BrewingLog
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
        self.fields['date'].widget.attrs['data-provide'] = 'datepicker'
        self.fields['date'].widget.attrs['data-date-format'] = 'dd.mm.yyyy'
        self.fields['date'].widget.attrs['data-date-language'] = 'ru'
        self.fields['note'].widget.attrs['class'] = 'form-control note'


class WaterTargetAddForm(AbstractAddForm):
    class Meta:
        model = WaterTargetProfile
        fields = '__all__'


class WaterOriginalAddForm(AbstractAddForm):
    class Meta:
        model = WaterOriginalProfile
        fields = '__all__'


class WaterIngredientAddForm(AbstractAddForm):
    class Meta:
        model = WaterIngredient
        fields = '__all__'


class PrimingAddForm(AbstractAddForm):
    class Meta:
        model = Priming
        fields = '__all__'


class FermentationGuidelinesAddForm(AbstractAddForm):
    class Meta:
        model = FermentationGuidelines
        fields = '__all__'

    def clean_step_temp(self):
        step_temp = self.cleaned_data.get('temp')
        if step_temp:
            return step_temp
        raise forms.ValidationError(_("Required field"), code='invalid')


MashFormSet = forms.inlineformset_factory(Recipe,
                                          MashGuidelines,
                                          form=MashGuidelinesAddForm,
                                          extra=0, min_num=1, max_num=10, can_delete=True)

GrainFormSet = forms.inlineformset_factory(Recipe,
                                           GrainIngredients,
                                           form=GrainIngredientsAddForm,
                                           extra=0, min_num=1, max_num=10, can_delete=True)

FermentableFormSet = forms.inlineformset_factory(Recipe,
                                                 FermentableIngredients,
                                                 form=FermentableIngredientsAddForm,
                                                 extra=0, min_num=1, max_num=10, can_delete=True)

HopsFormSet = forms.inlineformset_factory(Recipe,
                                          HopsIngredients,
                                          form=HopsIngredientsAddForm,
                                          extra=0, min_num=1, max_num=20, can_delete=True)

MiscFormSet = forms.inlineformset_factory(Recipe,
                                          MiscIngredients,
                                          form=MiscIngredientsAddForm,
                                          extra=0, min_num=1, max_num=20, can_delete=True)

YeastsFormSet = forms.inlineformset_factory(Recipe,
                                            YeastsIngredients,
                                            form=YeastsIngredientsAddForm,
                                            extra=0, min_num=1, max_num=2, can_delete=True)

LogFormSet = forms.inlineformset_factory(Recipe,
                                         BrewingLog,
                                         form=BrewingLogAddForm,
                                         extra=0, min_num=1, max_num=20, can_delete=True)

WaterTargetFormSet = forms.inlineformset_factory(Recipe,
                                                 WaterTargetProfile,
                                                 form=WaterIngredientAddForm,
                                                 min_num=1, max_num=1, can_delete=False)

WaterOriginalFormSet = forms.inlineformset_factory(Recipe,
                                                   WaterOriginalProfile,
                                                   form=WaterOriginalAddForm,
                                                   min_num=1, max_num=1, can_delete=False)

WaterIngredientFormSet = forms.inlineformset_factory(Recipe,
                                                     WaterIngredient,
                                                     form=WaterIngredientAddForm,
                                                     extra=0, min_num=1, max_num=20, can_delete=True)

PrimerFormSet = forms.inlineformset_factory(Recipe,
                                            Priming,
                                            form=PrimingAddForm,
                                            min_num=1, max_num=1, can_delete=False)

FermentationFormSet = forms.inlineformset_factory(Recipe,
                                                  FermentationGuidelines,
                                                  form=FermentationGuidelinesAddForm,
                                                  extra=0, min_num=1, max_num=20, can_delete=True)


class UserForm(AbstractAddForm):
    class Meta:
        model = BrewUser
        fields = '__all__'


class SendMessageForm(AbstractAddForm):
    class Meta:
        model = Message
        fields = '__all__'