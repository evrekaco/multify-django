from django.contrib import admin

# Register your models here.

from models import FoursquareApp, Client, Device, SubscribeEmail, Multify, Subscriber, ActivityRecord, CheckinRecord


class CustomModelAdminMixin(object):
    def __init__(self, model, admin_site):
        self.list_display = [field.name for field in model._meta.fields if field.name != "id"]
        super(CustomModelAdminMixin, self).__init__(model, admin_site)


@admin.register(FoursquareApp)
class FoursquareAppAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    pass


@admin.register(Client)
class ClientAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    pass


@admin.register(Device)
class DeviceAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    pass


@admin.register(SubscribeEmail)
class SubscriberEmailAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    pass


@admin.register(Subscriber)
class SubscriberAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    pass


@admin.register(Multify)
class MultifyAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    pass


@admin.register(ActivityRecord)
class ActivityRecordAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    pass

@admin.register(CheckinRecord)
class CheckinRecordAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    pass


