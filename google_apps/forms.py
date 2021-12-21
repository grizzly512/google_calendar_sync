from django import forms
from django.utils.translation import ugettext_lazy as _

from .models.calendar import Company, Hall


class CompanyCreateForm(forms.ModelForm):

    class Meta:
        model = Company
        fields = ('name', )


class HallEnableForm(forms.ModelForm):

    class Meta:
        model = Hall
        fields = ('given_name', )


class ConfirmForm(forms.Form):
    confirm = forms.BooleanField(
        label=_('Please confirm you wish to proceed'),
        required=True
    )

    def clean(self) -> None:
        cleaned_data = super(ConfirmForm, self).clean()
        confirm = cleaned_data.get("confirm")

        if not confirm:
            raise forms.ValidationError(
                _('You must confirm to proceed!')
            )
