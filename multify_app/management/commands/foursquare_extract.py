# coding=utf-8
from __future__ import unicode_literals
from datetime import datetime
from django.utils import timezone
from django.core.management.base import BaseCommand

from multify_app.models import Multify, CheckinRecord
import csv


class Command(BaseCommand):
    help = 'Multify verilerini extract eder'

    def handle(self, *args, **options):
        multify_list = Multify.objects.all()
        print "Multify Sec:"
        for idx, multify in enumerate(multify_list):
            print (("\t %d - " % idx) + multify.client.venue_name).encode('utf-8')

        try:
            choosen = int(raw_input("secim: "))
        except:
            print "Sayi girilmedi sanirim"
            return

        query_dict = {}
        string_start_date = raw_input("GUN.AY.YIL seklinde baslangic tarihi girin. En bastan baslayacaksa -1 yazin.")
        if string_start_date == "-1":
            start_date = None
        else:
            splitted = string_start_date.split(".")
            start_date = datetime(int(splitted[2]), int(splitted[1]), int(splitted[0])).date()
            query_dict['checkin_date__gte'] = start_date

        string_start_date = raw_input("GUN.AY.YIL seklinde bitis tarihi girin. En sona kadar ise -1 yazin.")
        if string_start_date == "-1":
            end_date = None
        else:
            splitted = string_start_date.split(".")
            end_date = datetime(int(splitted[2]), int(splitted[1]), int(splitted[0])).date()
            query_dict['checkin_date__lte'] = end_date

        multify = multify_list[choosen]

        query_dict['multify'] = multify
        checkin_records = CheckinRecord.objects.filter(**query_dict).order_by('-checkin_date')

        filename = multify.client.venue_name + "_records_" + (start_date if start_date else "NONE") + "_to_" + (
        end_date if end_date else "NONE")
        csvwriter = csv.writer(open("%s.csv" % filename, 'wb'))
        headers = ['name', 'surname', 'fsq_id', 'checkin_date', 'gender']
        csvwriter.writerow(headers)

        for obj in checkin_records.iterator():
            row = []
            for field in headers:
                val = getattr(obj, field)
                if callable(val):
                    val = val()
                if type(val) == unicode:
                    val = val.encode("utf-8")
                row.append(val)
            csvwriter.writerow(row)

        print checkin_records.count(), "records dumped to"
        print ("'" + filename + ".csv'").encode('utf-8')

