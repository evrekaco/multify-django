from django.contrib import admin

# Register your models here.

from models import FoursquareApp, Client, Device, Multify, Subscriber, ActivityRecord, CheckinRecord,MultifyOrder,OrderShipmentPrice


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
    list_filter = ('multify__client__venue_name','checkin_date')
    pass


@admin.register(MultifyOrder)
class CheckinRecordAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    pass

@admin.register(OrderShipmentPrice)
class CheckinRecordAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    pass
