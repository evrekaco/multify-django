# coding=utf-8
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from models import Subscriber, Multify

from django import forms


class SubscribeForm(forms.ModelForm):
    accept_tos = forms.BooleanField(label="I accept Terms of Service")

    class Meta:
        model = Subscriber
        widgets = {"message": forms.Textarea}
        fields = {"venue_name", "name", "phone", "email", "message", "accept_tos"}

    def clean_accept_tos(self):
        if not self.cleaned_data['accept_tos']:
            raise forms.ValidationError('You have to accept TOS')
        return self.cleaned_data['accept_tos']


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
                self._errors["username"] = self.error_class(["Bu kullanici kayıtlı değil"])
                return self.cleaned_data

            user = authenticate(username=self.username, password=self.password)
            if user is None:
                self._errors["password"] = self.error_class(["Hatalı şifre girdiniz"])
        return self.cleaned_data


class MultifyCorrectForm(forms.Form):
    corrected_count = forms.IntegerField()

    def __init__(self, user, *args, **kwargs):
        super(MultifyCorrectForm, self).__init__(*args, **kwargs)
        self.fields['multify'] = forms.ModelChoiceField(queryset=Multify.objects.filter(client__user=user),empty_label="(Seciniz)")

    def clean(self):
        self.corrected_count = self.cleaned_data.get('corrected_count')
        if self.corrected_count > 999999 or self.corrected_count < 0:
            self._errors["corrected_count"] = self.error_class(["Sayi 6 haneden fazla yada negatif olamaz"])
            return self.cleaned_data
        return self.cleaned_data

