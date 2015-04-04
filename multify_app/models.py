# -*- coding: utf-8 -*-
from datetime import datetime
import json
from django.contrib.auth.models import User
from django.db import models
from django_countries.fields import CountryField

# Create your models here.
from django.db.models import Model
from django.utils.translation import gettext_lazy as _



class Client(models.Model):
    user = models.ForeignKey(User)
    venue_name = models.CharField(max_length=255,blank=True,null=True, verbose_name=_("Venue Name"))
    auth_token = models.CharField(max_length=255,blank=True,null=True, verbose_name=_("Client Auth Token"))
    foursquare_code = models.CharField(max_length=255, blank=True, null=True,unique=True,verbose_name=_("FourSquare Code"))

    def __unicode__(self):
        return self.venue_name

    def multify_instances(self):
        return Multify.objects.filter(client=self)

class Device(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Device Name"))
    device_id = models.CharField(max_length=255, blank=True, null=True, unique=True, verbose_name=_("Device ID"))
    def __unicode__(self):
        return self.name + " : " + self.device_id


class FoursquareApp(models.Model):
    client_ID = models.CharField(max_length=255,blank=False,null=False, verbose_name=_("Client ID"))
    client_Secret = models.CharField(max_length=255,blank=True,null=True,verbose_name=_("Client Secret"))
    app_name = models.CharField(max_length=255,blank=True,null=True, verbose_name=_("Application Name"))
    usage_count = models.PositiveIntegerField(blank=True,null=True , verbose_name=_("Usage Count"))

    def __unicode__(self):
        return self.app_name

class Multify(models.Model):
    device = models.OneToOneField(Device)
    client = models.ForeignKey(Client)
    checkin_count = models.PositiveIntegerField(blank=True,null=True, verbose_name=_("Check-in Count"))
    unique_users = models.PositiveIntegerField(blank=True,null=True, verbose_name=_("Unique Count"))
    application = models.ForeignKey(FoursquareApp)
    last_updated = models.DateTimeField(default=datetime.now, blank=True)

    class Meta:
        unique_together = ("client", "device")

    def __unicode__(self):
        return "Device: " + self.device.name+ "  Client: " + str(self.client) + "  Used Application: " + str(self.application)


class Subscriber(models.Model):
    venue_name = models.CharField(max_length=255,blank=False,null=False, verbose_name=_("Venue Name"))
    name = models.CharField(max_length=255,blank=False,null=False, verbose_name=_("Name"))
    email = models.EmailField(max_length=100,blank=False,null=False, verbose_name=_("Email"))
    phone = models.CharField(max_length=30 ,blank=False,null=False, verbose_name=_("Phone"))
    message = models.CharField(max_length=255,blank=False,null=False, verbose_name=_("Message"))

    def __unicode__(self):
        return self.venue_name + " : " + self.name + " : " + self.email + " : " + self.phone

class ActivityRecord(models.Model):
    type = models.CharField(max_length=30,blank=False,null=False, verbose_name=_("Type"))
    content = models.CharField(max_length=255,blank=False,null=False, verbose_name=_("Data"))
    date = models.DateTimeField(default=datetime.now, blank=True)


class UserGender():
    MALE = 1
    FEMALE = 2
    NOT_TO_SPECIFY = 3

    CHOICES = (
        (MALE, _("Male")),
        (FEMALE, _("Female")),
        (NOT_TO_SPECIFY, _("Not Specified")),
    )

class CheckinRecord(models.Model):
    multify = models.ForeignKey(Multify)
    name = models.CharField(max_length=30,blank=True,null=True, verbose_name=_("Name"))
    surname = models.CharField(max_length=30,blank=True,null=True, verbose_name=_("Surname"))
    fsq_id = models.CharField(max_length=30,blank=False,null=False, default="", verbose_name=_("FSQ User ID"))
    checkin_date = models.DateTimeField(blank=False,null=False,verbose_name=_("Check-in DateTime"))
    profile_picture_url = models.TextField(blank=True,null=True, verbose_name=_("Profile Pic. Url"))
    gender = models.IntegerField(choices=UserGender.CHOICES, default=UserGender.NOT_TO_SPECIFY, verbose_name=_("Gender"))

    class Meta:
        unique_together = ("id", "checkin_date")

    def __unicode__(self):
        name = ""
        if self.name:
            name += self.name
        if self.surname:
            name += self.surname

        return "NAME: " + name + "\tDATE: " +str(self.checkin_date)

    def to_dict(self,index=None):
        context = {}
        if self.name:
            context["name"] = self.name
        else:
            context["name"] = ""
        if self.surname:
            context["surname"] = self.surname
        else:
            context["surname"] = ""
        if self.checkin_date:
            context["checkin_date"] = self.checkin_date.isoformat()
        else:
            context["checkin_date"] = ""
        if self.profile_picture_url:
            context["pic_url"] = self.profile_picture_url
        else:
            context["pic_url"] = ""
        if index:
            context["index"] = str(index)
        else:
            context["index"] = ""
        return context


class OrderShipmentPrice(models.Model):
    country = CountryField(verbose_name=_("Country"), unique=True)
    shipment_price = models.PositiveIntegerField(verbose_name=_("Shipment Cost"))

class MultifyOrder(models.Model):
    order_count = models.IntegerField(choices=[(x,str(x)) for x in range(1,6)], default=1, verbose_name=_("Order Count"))

    first_name = models.CharField(max_length=30, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=30, verbose_name=_("Last Name"))
    company_name = models.CharField(max_length=30,blank=True,null=True, verbose_name=_("Company Name"))
    shipping_address = models.CharField(max_length=100, verbose_name=_("Address Line"))
    shipping_address_2 = models.CharField(max_length=100,blank=True,null=True, verbose_name=_("Address Line 2"))
    shipping_zip = models.CharField(max_length=30,blank=True,null=True, verbose_name=_("Zip"))
    shipping_city = models.CharField(max_length=30,blank=True,null=True, verbose_name=_("City"))
    shipping_state = models.CharField(max_length=30,blank=True,null=True, verbose_name=_("State"))

    shipping_country = CountryField(verbose_name=_("Country"))

    billing_address = models.CharField(max_length=100, verbose_name=_("Address Line"))
    billing_address_2 = models.CharField(max_length=100,blank=True,null=True, verbose_name=_("Address Line 2"))
    billing_zip = models.CharField(max_length=30,blank=True,null=True, verbose_name=_("Zip"))
    billing_city = models.CharField(max_length=30,blank=True,null=True, verbose_name=_("City"))
    billing_state = models.CharField(max_length=30,blank=True,null=True, verbose_name=_("State"))

    billing_country = CountryField(verbose_name=_("Country"))

    contact_mobile = models.CharField(max_length=30,blank=True,null=True, verbose_name=_("Contact(mobile)"))
    contact_email = models.EmailField(verbose_name=_("Contact(e-mail)"))

    transaction_id = models.CharField(max_length=100, blank=True, verbose_name="Transaction ID", null=True)
    external_id = models.CharField(max_length=200, blank=True, verbose_name="External ID", null=True)
    reference_id = models.CharField(max_length=100, blank=True, verbose_name="Reference ID", null=True)
    paid_amount = models.PositiveIntegerField(null=True, blank=True, verbose_name="Amount Paid")
    currency = models.CharField(max_length=10, blank=True, verbose_name="Currency", null=True)
    admin_comment = models.TextField(verbose_name="Comments")
    customer_comment = models.TextField(verbose_name=_("Comments"),blank=True,null=True)

    payment_done = models.BooleanField(default=False, verbose_name="Payment Successful")




