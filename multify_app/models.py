from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django.db.models import Model

class Client(models.Model):
    user = models.ForeignKey(User)
    auth_token = models.CharField(max_length=255,blank=True,null=True, verbose_name="Client Auth Token")
    foursquare_code = models.CharField(max_length=255, blank=True, null=True,unique=True,verbose_name="FourSquare Code")

class Device(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Device Name")
    device_id = models.CharField(max_length=255, blank=True, null=True, unique=True, verbose_name="Device ID")


class FoursquareApp(models.Model):
    client_ID = models.CharField(max_length=255,blank=False,null=False, verbose_name="Client ID")
    client_Secret = models.CharField(max_length=255,blank=True,null=True,verbose_name="Client Secret")
    app_name = models.CharField(max_length=255,blank=True,null=True, verbose_name="Application Name")
    usage_count = models.PositiveIntegerField(blank=True,null=True , verbose_name="Usage Count")

class Multify(models.Model):
    device = models.ForeignKey(Device)
    client = models.ForeignKey(Client)
    checkin_count = models.PositiveIntegerField(blank=True,null=True, verbose_name="Check-in Count")
    application = models.ForeignKey(FoursquareApp)

    class Meta:
        unique_together = ("client", "device")

class SubscribeEmail(models.Model):
    email = models.EmailField(blank=False, null=False)

class Subscriber(models.Model):
    venue_name = models.CharField(max_length=255,blank=False,null=False, verbose_name="Venue Name")
    name = models.CharField(max_length=255,blank=False,null=False, verbose_name="Name")
    email = models.EmailField(max_length=255,blank=False,null=False, verbose_name="Email")
    phone = models.CharField(max_length=30 ,blank=False,null=False, verbose_name="Phone")
    message = models.EmailField(max_length=255,blank=False,null=False, verbose_name="Message")

