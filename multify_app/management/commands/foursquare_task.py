# -*- coding: utf-8 -*-
from datetime import datetime
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
                self.stdout.write('Current Multify: %s' % str(multify))
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

                    print response


                    if multify.client.foursquare_code:
                        try:
                            print "startAt:", int(mktime(multify.last_updated.timetuple())) , multify.last_updated
                            stats = fsq_client.venues.stats(multify.client.foursquare_code,params={"startAt":int(mktime(multify.last_updated.timetuple()))})
                            for visitor in stats["stats"]["recentVisitors"]:
                                new_rec, created = CheckinRecord.objects.get_or_create(multify=multify, checkin_date=datetime.fromtimestamp(visitor["lastCheckin"]), fsq_id=visitor["user"]["id"].encode('utf-8'))
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
                        except Exception as e:
                            print str(e)

                    if changed:
                        multify.last_updated = datetime.now()
                    multify.save()

            sleep(10)
