# coding=utf-8
from __future__ import unicode_literals
import json
import urllib
import urllib2
import datetime
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage, send_mail
from django.contrib.auth import authenticate, login
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
import foursquare
from ipware.ip import get_ip
import requests
# Create your views here.
from forms import SubscribeForm, ClientLoginForm, MultifyCorrectForm, MultifyOrderForm, ClientVenueCodeForm
from models import Client, Multify, ActivityRecord, Device, CheckinRecord, OrderShipmentPrice, MultifyOrder
from  django_project import settings

from django.template.defaultfilters import slugify
from django_project.settings import IYZICO_API_KEY, IYZICO_SECRET, SITE_URL, FSQ_PUSH_SECRET
from django.utils.translation import ugettext_lazy as _

from django.utils import timezone


def index(request, form=None):
    # Anasayfa
    if form:
        subs_form = form
    else:
        subs_form = SubscribeForm()
    return render(request, 'home.html', {"subscribe_form": subs_form})


def save_subscriber_record(request):
    # Maillist save
    if request.method == "POST":
        form = SubscribeForm(request.POST)
        if form.is_valid():
            m = form.save()
            msg_plain = render_to_string('email/subscriber_alert/email.txt', {'message': m})
            msg_html = render_to_string('email/subscriber_alert/email.html', {'message': m})

            send_mail(
                'Yeni Subscriber/contact form dolduruldu.',
                msg_plain,
                'no-reply@multify.co',
                ['info@multify.co', 'umutcan.duman@gmail.com', 'gokcennurlu@gmail.com'],
                html_message=msg_html,
                fail_silently=False
            )

            return index(request)
        else:
            return index(request, form)
    else:
        return index(request)


def client_login(request):
    # login view
    if request.method == "POST":
        form = ClientLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(username=username, password=password)
            if user and user.is_active:
                login(request, user)
                print "User Logged in"
                return redirect(reverse('multify_app.views.client_home'))
            else:
                # TODO user aktif degil yada yok hatasi
                print "User not active or None"
                pass
        else:
            print "Form not valid"
            return render(request, 'client/login.html', {"login_form": form})
    else:
        return render(request, 'client/login.html', {"login_form": ClientLoginForm()})


def client_home(request, error=None, success=None):
    # client Home page
    if not request.user.is_authenticated():
        return redirect(reverse('multify_app.views.client_login'))
    if request.user.is_staff:
        return redirect("/admin")
    try:
        user = request.user._wrapped if hasattr(request.user, '_wrapped') else request.user
        client = Client.objects.get(user=user)
    except:
        return index(request)
    return render(request, 'client/home.html', {"client": client, "error": error, "success": success})


def change_venue_code(request):
    if not request.user.is_authenticated():
        return redirect(reverse('multify_app.views.client_login'))
    if request.user.is_staff:
        return redirect("/admin")

    try:
        client_obj = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        return render(request, 'client/change_venue.html', {"error": _("Client Object does not exist")})

    if request.method == "GET":
        form = ClientVenueCodeForm(instance=client_obj)
        return render(request, 'client/change_venue.html', {"form": form})
    else:
        form = ClientVenueCodeForm(request.POST, instance=client_obj)
        if form.is_valid():
            client_obj_temp = form.save()
            try:
                multify = Multify.objects.get(client=client_obj_temp)
            except Exception as e:
                client_obj_temp.venue_name = "<Bos>"
                client_obj_temp.save()
                new_form = ClientVenueCodeForm(instance=client_obj_temp)
                return render(request, 'client/change_venue.html',
                              {"form": new_form, "error": _("There is no connected Multify")})

            try:
                fsq_client = foursquare.Foursquare(client_id=multify.application.client_ID,
                                                   client_secret=multify.application.client_Secret)
                name = fsq_client.venues(client_obj_temp.foursquare_code)["venue"]["name"]
            except Exception as e:
                client_obj_temp.venue_name = "<Bos>"
                client_obj_temp.save()
                new_form = ClientVenueCodeForm(instance=client_obj_temp)
                return render(request, 'client/change_venue.html',
                              {"form": new_form, "error": _("Foursquare App Configuration error") + ": " + str(e)})

            client_obj_temp.venue_name = name.encode('utf-8')
            client_obj_temp.save()
            new_form = ClientVenueCodeForm(instance=client_obj_temp)
            return render(request, 'client/change_venue.html', {"form": new_form, "success": _("Changed Succesfully")})
        else:
            return render(request, 'client/change_venue.html', {"form": form})


def multify_correct(request):
    # client Multify imi dogrula sayfasi
    if not request.user.is_authenticated():
        return redirect(reverse('multify_app.views.client_login'))
    if request.user.is_staff:
        return redirect("/admin")

    try:
        user = request.user._wrapped if hasattr(request.user, '_wrapped') else request.user
        client = Client.objects.get(user__pk=user.pk)
    except:
        return index(request)

    if request.method == "POST":
        user = request.user._wrapped if hasattr(request.user, '_wrapped') else request.user
        form = MultifyCorrectForm(user, request.POST)
        if form.is_valid():
            try:
                url = "https://api.spark.io/v1/devices/%s/Changer" % form.cleaned_data['multify'].device.device_id
                payload = {'access_token': settings.SPARK_ACCESS_TOKEN,
                           'args': str(form.cleaned_data["corrected_count"])}
                r = requests.post(url, data=payload)
                print r.text
            except Exception as e:
                rec = ActivityRecord(type="Sayac Guncellemesi Hata",
                                     content=str(form.cleaned_data['multify']) + " :::  HATA: " + str(e))
                rec.save()
                return client_home(request, error="Sayac Guncellemede hata: " + str(e))

            rec = ActivityRecord(type="Sayac Guncellemesi Basarili", content=str(form.cleaned_data['multify']))
            rec.save()
            return client_home(request, success="Sayac basariyle guncellendi")
        else:
            return render(request, 'client/correct.html',
                          {"client": client, "correct_form": form})
    else:
        user = request.user._wrapped if hasattr(request.user, '_wrapped') else request.user
        return render(request, 'client/correct.html',
                      {"client": client, "correct_form": MultifyCorrectForm(user)})


def foursquare_token_generate(request):
    if not request.user.is_authenticated():
        return redirect(reverse('multify_app.views.client_login'))
    if request.user.is_staff:
        return redirect("/admin")

    try:
        user = request.user._wrapped if hasattr(request.user, '_wrapped') else request.user
        multify = Multify.objects.filter(client__user=user)
        if len(multify) > 0:
            multify = multify[0]
    except:
        return index(request)

    print settings.SITE_URL + reverse('multify_app.views.after_fsq_auth')
    try:
        fsq_client = foursquare.Foursquare(client_id=multify.application.client_ID,
                                           client_secret=multify.application.client_Secret,
                                           redirect_uri=settings.SITE_URL + reverse('multify_app.views.after_fsq_auth'))
        auth_uri = fsq_client.oauth.auth_url()
        print auth_uri
    except Exception as e:
        rec = ActivityRecord(type="Foursquare Token Error", content=str(multify) + " ::: HATA: " + str(e))
        rec.save()
        return client_home(request, error="Foursquare Token Guncellemesinde Hata: " + str(e))
    return redirect(auth_uri)


def after_fsq_auth(request):
    if request.method == "GET":
        print request.user
        user = request.user._wrapped if hasattr(request.user, '_wrapped') else request.user
        multify = Multify.objects.filter(client__user=user)
        if len(multify) > 0:
            multify = multify[0]
        else:
            return client_home(request, error="Henuz Multify Kaydiniz yok?")
        # Interrogate foursquare's servers to get the user's access_token
        try:
            fsq_client = foursquare.Foursquare(client_id=multify.application.client_ID,
                                               client_secret=multify.application.client_Secret,
                                               redirect_uri=settings.SITE_URL + reverse(
                                                   'multify_app.views.after_fsq_auth'))
            returned_code = request.GET.get("code", "")
            print returned_code
            access_token = fsq_client.oauth.get_token(returned_code)
        except Exception as e:
            rec = ActivityRecord(type="Foursquare Token Error", content=str(multify) + " ::: HATA: " + str(e))
            rec.save()
            return client_home(request, error="FOURSQUARE ERROR: " + str(e))
        multify.client.auth_token = access_token
        multify.client.save()
        return client_home(request, success="Foursquare Token Basariyla Alindi")
    else:
        return client_home(request, error="Post Request bu adrese yapilamaz")


def get_device_data(request, device_id=None):
    if request.method == "POST":
        return HttpResponse(json.dumps({"state": "fail", "message": "Can not POST request here"}))
    else:
        if not device_id:
            return HttpResponse(json.dumps({"state": "fail", "message": "Device ID missing"}))
        else:
            multify = Multify.objects.filter(device__device_id=device_id)
            if len(multify) == 0:
                return HttpResponse(json.dumps({"state": "fail", "message": "No device found with this ID"}))
            else:
                multify = multify[0]

            rec = CheckinRecord.objects.filter(multify=multify).order_by('-checkin_date')
            if len(rec) > 0:
                rec = rec[0]
                the_dict = rec.to_dict()
                the_dict["check_in_count"] = multify.checkin_count
                return HttpResponse(
                    json.dumps({"state": "success", "message": "Succesfully got last user data", "data": the_dict}))
            else:
                return HttpResponse(json.dumps({"state": "fail", "message": "No single checkin found for this ID"}))


def get_device_data_raw(request, device_id=None):
    if request.method == "POST":
        return HttpResponse("error")
    else:
        if not device_id:
            return HttpResponse("no_device_id")
        else:
            multify = Multify.objects.filter(device__device_id=device_id)
            if len(multify) == 0:
                return HttpResponse("multify_not_found")
            else:
                multify = multify[0]
                return HttpResponse(str(multify.checkin_count))


def get_checkins(request):
    if request.method == "GET":
        multify = Multify.objects.filter(client__user=request.user)
        if len(multify) > 0:
            multify = multify[0]
        else:
            return client_home(request, error="Henuz Multify Kaydiniz yok?")
        rec = CheckinRecord.objects.filter(multify=multify).order_by('-checkin_date')[:10]
        response = {"data": [x.to_dict(multify.checkin_count - idx) for idx, x in enumerate(rec)]}
        return HttpResponse(json.dumps(response))


@csrf_exempt
def push_welcomer(request):
    if "secret" in request.POST and request.POST["secret"] == FSQ_PUSH_SECRET:
        # print "Yay! a valid PUSH from fsq.."
        if "checkin" in request.POST and "venue" in request.POST["checkin"]:
            gender_dict = {"male": 1, "female": 2}

            checkin = json.loads(request.POST["checkin"])
            #print checkin

            venue_code = checkin["venue"]["id"]
            venue_name = checkin["venue"]["name"]


            print "POST from", str(get_ip(request))
            print "Checkin AT", venue_name, " - Looking for multifys"


            multifys = Multify.objects.filter(client__foursquare_code=venue_code)
            if multifys.count() > 0:
                #print "Venue code to multify result:", multifys
                for multify in multifys:
                    try:
                        print "Updating Public Data.."
                        response = checkin["venue"]["stats"]
                        changed = False
                        if "checkinsCount" in response:
                            multify.checkin_count = response["checkinsCount"]
                            changed = True
                        if "usersCount" in response:
                            multify.unique_users = response["usersCount"]
                            changed = True

                        if changed:
                            print response
                            multify.last_updated = datetime.datetime.now(tz=timezone.get_current_timezone())
                            multify.save()
                            print "Public data updated.."

                        print "ADDING checkin to: ", multify.client.venue_name
                        new_rec, created = CheckinRecord.objects.get_or_create(multify=multify,
                                                                               checkin_date=datetime.datetime.fromtimestamp(
                                                                                   checkin["createdAt"],
                                                                                   timezone.get_current_timezone()),
                                                                               fsq_id=checkin["user"]["id"].encode('utf-8'))
                        if "firstName" in checkin["user"]:
                            new_rec.name = checkin["user"]["firstName"]
                        if "lastName" in checkin["user"]:
                            new_rec.surname = checkin["user"]["lastName"]
                        if "gender" in checkin["user"]:
                            new_rec.gender = gender_dict[checkin["user"]["gender"]] if checkin["user"][
                                                                                           "gender"] in gender_dict else 3
                        if "photo" in checkin["user"] and "prefix" in checkin["user"]["photo"] and "suffix" in \
                                checkin["user"]["photo"]:
                            new_rec.profile_picture_url = checkin["user"]["photo"]["prefix"] + "original" + \
                                                          checkin["user"]["photo"]["suffix"]

                        if created:
                            print "\tNEW CHECKIN!", str(new_rec)
                        else:
                            print "\tDUPLICATE AVOIDED"
                        new_rec.save()
                    except Exception as e:
                        print str(e)
            else:
                print "We don't have a multify for this code:", venue_code, "and name:", venue_name
        else:
            print "No checkin info in this push.."
    else:
        print "BAD PUSH"
    return HttpResponse("Hola")


def order_form(request, message=None):
    # TODO TURKCE ve INGILIZCE formlar eklenmeli, CURRENCY, BASE FIYAT
    if request.method == "POST":
        form = MultifyOrderForm(request.POST)
        if form.is_valid():
            order = form.save()
            order.external_id = slugify(
                order.first_name + order.last_name + datetime.datetime.now().isoformat() + " ordercount " + str(
                    order.order_count))
            shipping_models = OrderShipmentPrice.objects.filter(country=order.shipping_country)
            if len(shipping_models) > 0:
                shipment_cost = shipping_models[0].shipment_price
            else:
                shipment_cost = 50

            multiplier = 1

            try:
                cur = urllib2.urlopen('http://rate-exchange.appspot.com/currency?from=EUR&to=USD')
                cur_dict = json.loads(cur.read())
                multiplier = cur_dict['rate']
                shipment_cost = int(shipment_cost * multiplier)
                print multiplier
            except Exception as e:
                print "error at currency parsing", str(e)

            if form.cleaned_data["form_currency"] == "TRY":
                amount = str(((2000 + shipment_cost) * 100) * order.order_count)
                base_amount = 2000
                currency_text = "TL"
                without_shipment = order.order_count * 2000
                full_shipment = order.order_count * shipment_cost
                print order.order_count
            else:
                amount = str(((700 + shipment_cost) * 100) * order.order_count)
                base_amount = 700
                currency_text = "$"
                without_shipment = order.order_count * 700
                full_shipment = order.order_count * shipment_cost
                print order.order_count
            data = {
                # TODO fix these values
                'api_id': IYZICO_API_KEY
                , 'secret': IYZICO_SECRET
                , 'external_id': order.external_id
                , 'mode': 'live'
                , 'type': 'CC.DB'
                , 'return_url': SITE_URL + reverse("multify_app.views.after_payment_page")
                , 'amount': amount
                , 'currency': form.cleaned_data["form_currency"]
                , 'descriptor': ''
                , 'item_id_1': 'foursquare_device'
                , 'item_name_1': 'Multify Device'
                , 'item_unit_quantity_1': str(order.order_count)
                , 'item_unit_amount_1': '1'
                , 'customer_first_name': order.first_name.encode('utf-8')
                , 'customer_last_name': order.last_name.encode('utf-8')
                , 'customer_company_name': order.company_name.encode('utf-8')
                , 'customer_shipping_address_line_1': order.shipping_address.encode('utf-8')
                , 'customer_shipping_address_line_2': order.shipping_address_2.encode('utf-8')
                , 'customer_shipping_address_zip': order.shipping_zip.encode('utf-8')
                , 'customer_shipping_address_city': order.shipping_city.encode('utf-8')
                , 'customer_shipping_address_state': order.shipping_state.encode('utf-8')
                , 'customer_shipping_address_country': order.shipping_country.name
                , 'customer_billing_address_line_1': order.billing_address.encode('utf-8')
                , 'customer_billing_address_line_2': order.billing_address_2.encode('utf-8')
                , 'customer_billing_address_zip': order.billing_zip.encode('utf-8')
                , 'customer_billing_address_city': order.billing_city.encode('utf-8')
                , 'customer_billing_address_state': order.billing_state.encode('utf-8')
                , 'customer_billing_address_country': order.billing_country.name
                , 'customer_contact_phone': 'None'
                , 'customer_contact_mobile': order.contact_mobile
                , 'customer_contact_email': str(order.contact_email)
                , 'customer_contact_ip': str(get_ip(request)) if get_ip(request) else "None"
                , 'customer_language': 'tr'
                , 'installment': 'true'
            }
            resp = urllib2.urlopen('https://api.iyzico.com/v2/create', urllib.urlencode(data))
            resp_dict = json.loads(resp.read())
            if "response" in resp_dict and resp_dict['response']['state'] == "success":
                order.save()
                return render(request, 'payment.html',
                              {"order": order, "token": resp_dict['transaction_token'],
                               "amount": int(float(amount)) / 100, "base_amount": base_amount,
                               "cur_text": currency_text, "without_shipment": without_shipment,
                               "shipment_cost": shipment_cost,
                               "full_shipment": full_shipment})
            else:
                print resp_dict
                order.admin_comment = "ERROR: " + str(resp_dict)
                order.save()
                rec = ActivityRecord(type="PAYMENT HATA(before Payment)", content=str(resp_dict))
                rec.save()
                return render(request, 'order.html',
                              {"form": form, "message": "Error while connecting to payment system:" + str(resp_dict)})
        else:
            print "not valid", form.errors
            return render(request, 'order.html', {"form": form, "message": message})
    else:
        return render(request, 'order.html', {"form": MultifyOrderForm(), "message": message})


@csrf_exempt
def after_payment_page(request):
    if request.method == "GET":
        return index(request)
    else:
        if 'json' in request.POST:
            raw_data = request.POST.get('json')
            print raw_data
            try:
                data_as_dict = json.loads(raw_data)
                if data_as_dict['response']['state'] == "success":
                    data_as_dict = data_as_dict["transaction"]
                else:
                    rec = ActivityRecord(type="PAYMENT HATA(After Payment)", content=str(data_as_dict))
                    rec.save()
                    return order_form(request, "Payment Server error" + str(data_as_dict))
            except ValueError, e:
                return order_form(request, str(e))

            print "OK", data_as_dict
            external_id = data_as_dict['external_id']
            the_rec = MultifyOrder.objects.filter(external_id=external_id)
            if len(the_rec) > 0:
                order = the_rec[0]
                print "YES, now mark as paid this->", order
                order.transaction_id = data_as_dict['transaction_id']
                order.reference_id = data_as_dict['reference_id']
                order.paid_amount = int(float(data_as_dict['amount']))
                order.currency = data_as_dict['currency']
                order.payment_done = True
                order.save()

                # try:
                # email = EmailMessage('Order Successful', 'Payment successfully, from ' + order.first_name + " " + order.last_name, to=['akcoraberkay@gmail.com'])
                # email.send()
                #
                #     email = EmailMessage('Order Successful - Odeme Basarili', 'Thank you, ' + order.first_name + " " + order.last_name +"\nYour Transaction ID is: " + order.transaction_id, to=[order.contact_email])
                #     email.send()
                # except Exception:
                #     pass

                msg_plain_to_admin = render_to_string('email/order_complete_admin/email.txt', {'order': order})
                msg_html_to_admin = render_to_string('email/order_complete_admin/email.html', {'order': order})

                send_mail(
                    'Yeni Subscriber/contact form dolduruldu.',
                    msg_plain_to_admin,
                    'no-reply@multify.co',
                    ['info@multify.co', 'umutcan.duman@gmail.com',],
                    html_message=msg_html_to_admin,
                    fail_silently=True
                )

                return render(request, "success.html")
            else:
                return order_form(request, "Are you sure that you have a transaction id?")
        else:
            return order_form(request, "Payment Error.. No 'json' key in RESPONSE")
