# -*- coding: utf-8 -*-
from datetime import datetime
import json
from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django.db.models import Model

class Client(models.Model):
    user = models.ForeignKey(User)
    venue_name = models.CharField(max_length=255,blank=True,null=True, verbose_name="Venue Name")
    auth_token = models.CharField(max_length=255,blank=True,null=True, verbose_name="Client Auth Token")
    foursquare_code = models.CharField(max_length=255, blank=True, null=True,unique=True,verbose_name="FourSquare Code")

    def __unicode__(self):
        return self.venue_name

    def multify_instances(self):
        return Multify.objects.filter(client=self)

class Device(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Device Name")
    device_id = models.CharField(max_length=255, blank=True, null=True, unique=True, verbose_name="Device ID")
    def __unicode__(self):
        return self.name + " : " + self.device_id


class FoursquareApp(models.Model):
    client_ID = models.CharField(max_length=255,blank=False,null=False, verbose_name="Client ID")
    client_Secret = models.CharField(max_length=255,blank=True,null=True,verbose_name="Client Secret")
    app_name = models.CharField(max_length=255,blank=True,null=True, verbose_name="Application Name")
    usage_count = models.PositiveIntegerField(blank=True,null=True , verbose_name="Usage Count")

    def __unicode__(self):
        return self.app_name

class Multify(models.Model):
    device = models.OneToOneField(Device)
    client = models.ForeignKey(Client)
    checkin_count = models.PositiveIntegerField(blank=True,null=True, verbose_name="Check-in Count")
    unique_users = models.PositiveIntegerField(blank=True,null=True, verbose_name="Unique Count")
    application = models.ForeignKey(FoursquareApp)
    last_updated = models.DateTimeField(default=datetime.now, blank=True)

    class Meta:
        unique_together = ("client", "device")

    def __unicode__(self):
        return "Device: " + self.device.name+ "  Client: " + str(self.client) + "  Used Application: " + str(self.application)

class SubscribeEmail(models.Model):
    email = models.EmailField(blank=False, null=False)
    def __unicode__(self):
        return self.email

class Subscriber(models.Model):
    venue_name = models.CharField(max_length=255,blank=False,null=False, verbose_name="Venue Name")
    name = models.CharField(max_length=255,blank=False,null=False, verbose_name="Name")
    email = models.EmailField(max_length=100,blank=False,null=False, verbose_name="Email")
    phone = models.CharField(max_length=30 ,blank=False,null=False, verbose_name="Phone")
    message = models.CharField(max_length=255,blank=False,null=False, verbose_name="Message")

    def __unicode__(self):
        return self.venue_name + " : " + self.name + " : " + self.email + " : " + self.phone

class ActivityRecord(models.Model):
    type = models.CharField(max_length=30,blank=False,null=False, verbose_name="Type")
    content = models.CharField(max_length=255,blank=False,null=False, verbose_name="Data")
    date = models.DateTimeField(default=datetime.now, blank=True)


class UserGender():
    MALE = 1
    FEMALE = 2
    NOT_TO_SPECIFY = 3

    CHOICES = (
        (MALE, "Male"),
        (FEMALE, "Female"),
        (NOT_TO_SPECIFY, "Not Specified"),
    )

class CheckinRecord(models.Model):
    multify = models.ForeignKey(Multify)
    name = models.CharField(max_length=30,blank=True,null=True, verbose_name="Name")
    surname = models.CharField(max_length=30,blank=True,null=True, verbose_name="Surname")
    fsq_id = models.CharField(max_length=30,blank=False,null=False, default="", verbose_name="FSQ User ID")
    checkin_date = models.DateTimeField(blank=False,null=False,verbose_name="Check-in DateTime")
    profile_picture_url = models.TextField(blank=True,null=True, verbose_name="Profile Pic. Url")
    gender = models.IntegerField(choices=UserGender.CHOICES, default=UserGender.NOT_TO_SPECIFY,verbose_name="Gender")

    class Meta:
        unique_together = ("id", "checkin_date")

    def __unicode__(self):
        name = ""
        if self.name:
            name += self.name
        if self.surname:
            name += self.surname

        return "NAME: " + name + "\tDATE: " +str(self.checkin_date)

    def to_dict(self):
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
        return context

