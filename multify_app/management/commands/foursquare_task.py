# -*- coding: utf-8 -*-
from datetime import datetime
from django.utils import timezone
from time import sleep, time, mktime
from django.core.management.base import BaseCommand, CommandError
from django.core.urlresolvers import reverse
import foursquare
from multify_app.models import Multify, CheckinRecord
import django_project.settings


class Command(BaseCommand):
    args = '<poll_id poll_id ...>'
    help = 'Checks the Multify objects and updates them'



    def handle(self, *args, **options):
        gender_dict = {"male" : 1 , "female" : 2}
        list = Multify.objects.all()
        while True:
            for multify in list:
                self.stdout.write('Current Multify Client: %s' % str(multify.client.venue_name))
                self.stdout.write('Last Checked: %s' % str(multify.last_updated))
                if multify.client.auth_token:
                    changed = False
                    fsq_client = foursquare.Foursquare(access_token=multify.client.auth_token)
                    response = fsq_client.venues(multify.client.foursquare_code)["venue"]["stats"]

                    if "checkinsCount" in response:
                        multify.checkin_count = response["checkinsCount"]
                        changed = True
                    if "usersCount" in response:
                        multify.unique_users = response["usersCount"]
                        changed = True

                    print "Public data updated..", response


                    if multify.client.foursquare_code:
                        print "Trying to access more data using the token of", multify.client.venue_name
                        try:
                            #print "startAt:", int(mktime(multify.last_updated.timetuple())) , multify.last_updated
                            stats = fsq_client.venues.stats(multify.client.foursquare_code,params={"startAt":int(mktime(multify.last_updated.timetuple()))})
                            #stats = fsq_client.venues.stats(multify.client.foursquare_code)

                            for visitor in stats["stats"]["recentVisitors"]:
                                new_rec, created = CheckinRecord.objects.get_or_create(multify=multify, checkin_date=datetime.fromtimestamp(visitor["lastCheckin"], timezone.get_current_timezone()), fsq_id=visitor["user"]["id"].encode('utf-8'))
                                # print "RAW DATA:", visitor["lastCheckin"]
                                if "firstName" in  visitor["user"]:
                                    new_rec.name = visitor["user"]["firstName"]
                                if "lastName" in  visitor["user"]:
                                    new_rec.surname = visitor["user"]["lastName"]
                                if "gender" in  visitor["user"]:
                                    new_rec.gender = gender_dict[visitor["user"]["gender"]] if visitor["user"]["gender"] in gender_dict else 3
                                if "photo" in visitor["user"] and "prefix" in visitor["user"]["photo"] and "suffix" in visitor["user"]["photo"]:
                                    new_rec.profile_picture_url = visitor["user"]["photo"]["prefix"] + "original" + visitor["user"]["photo"]["suffix"]

                                if created:
                                    print "NEW CHECKIN!" , str(new_rec)
                                else:
                                    print "DUPLICATE AVOIDED"
                                new_rec.save()
                                # print "NEW_REC:", new_rec.checkin_date, new_rec.checkin_date.timetuple(),int(mktime(new_rec.checkin_date.timetuple())),"\n\n"
                            print "Succesfully accessed and processed data.."
                        except Exception as e:
                            print str(e)

                    if changed:
                        multify.last_updated = datetime.now(tz=timezone.get_current_timezone())
                    multify.save()
                print "\n"
            print "\n\n"
            sleep(10)
