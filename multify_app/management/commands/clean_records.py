# -*- coding: utf-8 -*-
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from multify_app.models import Multify, CheckinRecord


class Command(BaseCommand):
    args = '<poll_id poll_id ...>'
    help = 'Cleans the multify records'


    def handle(self, *args, **options):
        list = Multify.objects.all()
        CheckinRecord.objects.all().delete()
        for multify in list:
            multify.last_updated = datetime(2013, 1, 1)
            multify.save()
