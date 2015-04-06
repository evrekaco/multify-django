# coding=utf-8
from __future__ import unicode_literals
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from models import Subscriber, Multify, MultifyOrder

from django import forms
from django.utils.translation import ugettext_lazy as _


class SubscribeForm(forms.ModelForm):
    # accept_tos = forms.BooleanField(label="I accept Terms of Service")

    class Meta:
        model = Subscriber
        widgets = {"message": forms.Textarea}
        fields = {"venue_name", "name", "phone", "email", "message"}


class ClientLoginForm(forms.Form):
    username = forms.CharField(label="Username")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super(ClientLoginForm, self).__init__(*args, **kwargs)

    def clean(self):
        self.username = self.cleaned_data.get('username')
        self.password = self.cleaned_data.get('password')

        if self.username and self.password:
            try:
                user = User.objects.get(username=self.username)
            except:
                self._errors["username"] = self.error_class([_("Bu kullanici kayıtlı değil")])
                return self.cleaned_data

            user = authenticate(username=self.username, password=self.password)
            if user is None:
                self._errors["password"] = self.error_class([_("Hatalı şifre girdiniz")])
        return self.cleaned_data


class MultifyCorrectForm(forms.Form):
    multify = forms.ModelChoiceField(queryset=Multify.objects.all(), empty_label=_("(Seciniz)"))
    corrected_count = forms.IntegerField(label=_("Number seen on Multify"))
    def __init__(self, user, *args, **kwargs):
        super(MultifyCorrectForm, self).__init__(*args, **kwargs)
        user = user._wrapped if hasattr(user,'_wrapped') else user
        self.fields['multify'].queryset = Multify.objects.filter(client__user=user)


    def clean(self):
        self.corrected_count = self.cleaned_data.get('corrected_count')
        if self.corrected_count > 999999 or self.corrected_count < 0:
            self._errors["corrected_count"] = self.error_class([_("Sayi 6 haneden fazla yada negatif olamaz")])
            return self.cleaned_data
        return self.cleaned_data


class MultifyOrderForm(forms.ModelForm):
    accept_tos = forms.BooleanField(label=_("I accept Terms of Service"),required=True)
    class Meta:
        model = MultifyOrder
        fields = ("first_name", "last_name", "company_name", "shipping_address", "shipping_address_2", "shipping_zip",
                  "shipping_city", "shipping_state", "shipping_country", "billing_address", "billing_address_2",
                  "billing_zip", "billing_city", "billing_state", "billing_country", "contact_mobile", "contact_email",
                  "order_count", "customer_comment", "accept_tos")

    def clean_accept_tos(self):
        if not self.cleaned_data['accept_tos']:
            raise forms.ValidationError(_('You have to accept TOS'))
        return self.cleaned_data['accept_tos']

