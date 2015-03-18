from django.contrib import admin

# Register your models here.

from models import FoursquareApp,Client,Device,SubscribeEmail,Multify,Subscriber

admin.site.register(FoursquareApp)
admin.site.register(Client)
admin.site.register(Device)
admin.site.register(SubscribeEmail)
admin.site.register(Subscriber)
admin.site.register(Multify)


