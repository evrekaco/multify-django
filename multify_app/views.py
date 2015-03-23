import json
import urllib
import urllib2
from django.contrib.auth import authenticate, login
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import foursquare
import requests
# Create your views here.
from forms import SubscribeForm, ClientLoginForm, MultifyCorrectForm
from models import Client, Multify, ActivityRecord, Device, CheckinRecord
from  django_project import settings


def index(request, form=None):
    if form:
        subs_form = form
    else:
        subs_form = SubscribeForm()
    return render(request, 'home.html', {"subscribe_form": subs_form})


def save_subscriber_record(request):
    if request.method == "POST":
        form = SubscribeForm(request.POST)
        if form.is_valid():
            form.save()
            return index(request)
        else:
            return index(request, form)
    else:
        return index(request)


def client_login(request):
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


def client_home(request,error=None,success=None):
    if not request.user.is_authenticated():
        return redirect(reverse('multify_app.views.client_login'))
    if request.user.is_staff:
        return redirect("/admin")
    try:
        client = Client.objects.get(user=request.user)
    except:
        return index(request)
    return render(request, 'client/home.html', {"client": client , "error" : error, "success":success})


def multify_correct(request):
    if not request.user.is_authenticated():
        return redirect(reverse('multify_app.views.client_login'))
    if request.user.is_staff:
        return redirect("/admin")

    try:
        client = Client.objects.get(user=request.user)
    except:
        return index(request)

    if request.method == "POST":
        form = MultifyCorrectForm(request.user, request.POST)
        if form.is_valid():
            try:
                url = "https://api.spark.io/v1/devices/%s/Changer" % form.cleaned_data['multify'].device.device_id
                payload = {'access_token': settings.SPARK_ACCESS_TOKEN, 'args': str(form.cleaned_data["corrected_count"]) }
                r = requests.post(url,data=payload)
                print r.text
            except Exception as e:
                rec = ActivityRecord(type="Sayac Guncellemesi Hata", content=str(form.cleaned_data['multify']) + " :::  HATA: " + str(e))
                rec.save()
                return client_home(request,error="Sayac Guncellemede hata: " + str(e))

            rec = ActivityRecord(type="Sayac Guncellemesi Basarili", content=str(form.cleaned_data['multify']))
            rec.save()
            return client_home(request,success="Sayac basariyle guncellendi")
        else:
            return render(request, 'client/correct.html',
                          {"client": client, "correct_form": MultifyCorrectForm(request.user, request.POST)})
    return render(request, 'client/correct.html', {"client": client, "correct_form": MultifyCorrectForm(request.user)})


def foursquare_token_generate(request):
    if not request.user.is_authenticated():
        return redirect(reverse('multify_app.views.client_login'))
    if request.user.is_staff:
        return redirect("/admin")

    try:
        multify = Multify.objects.filter(client__user=request.user)
        if len(multify) > 0:
            multify = multify[0]
    except:
        return index(request)

    print settings.SITE_URL+reverse('multify_app.views.after_fsq_auth')
    try:
        fsq_client = foursquare.Foursquare(client_id=multify.application.client_ID, client_secret=multify.application.client_Secret , redirect_uri= settings.SITE_URL+reverse('multify_app.views.after_fsq_auth'))
        auth_uri = fsq_client.oauth.auth_url()
        print auth_uri
    except Exception as e:
        rec = ActivityRecord(type="Foursquare Token Error", content= str(multify) + " ::: HATA: " + str(e))
        rec.save()
        return client_home(request,error="Foursquare Token Guncellemesinde Hata: " + str(e))
    return redirect(auth_uri)

def after_fsq_auth(request):
    if request.method == "GET":
        multify = Multify.objects.filter(client__user=request.user)
        if len(multify) > 0:
            multify = multify[0]
        else:
            return client_home(request,error="Henuz Multify Kaydiniz yok?")
        # Interrogate foursquare's servers to get the user's access_token
        try:
            fsq_client = foursquare.Foursquare(client_id=multify.application.client_ID, client_secret=multify.application.client_Secret , redirect_uri= settings.SITE_URL+reverse('multify_app.views.after_fsq_auth'))
            returned_code = request.GET.get("code","")
            print returned_code
            access_token = fsq_client.oauth.get_token(returned_code)
        except Exception as e:
            rec = ActivityRecord(type="Foursquare Token Error", content = str(multify) + " ::: HATA: " + str(e))
            rec.save()
            return client_home(request,error="FOURSQUARE ERROR: " + str(e))
        multify.client.auth_token = access_token
        multify.client.save()
        return client_home(request, success="Foursquare Token Basariyla Alindi")
    else:
        return client_home(request,error="Post Request bu adrese yapilamaz")

def get_device_data(request, device_id = None):
    if request.method == "POST":
        return HttpResponse(json.dumps({"state":"fail" , "message":"Can not POST request here"}))
    else:
        if not device_id:
            return HttpResponse(json.dumps({"state":"fail" , "message":"Device ID missing"}))
        else:
            multify = Multify.objects.filter(device__device_id=device_id)
            if len(multify) == 0:
                return HttpResponse(json.dumps({"state":"fail" , "message":"No device found with this ID"}))
            else:
                multify = multify[0]

            rec = CheckinRecord.objects.filter(multify=multify).order_by('-checkin_date')
            if len(rec) > 0:
                rec = rec[0]
                the_dict = rec.to_dict()
                the_dict["check_in_count"] = multify.checkin_count
                return HttpResponse(json.dumps({"state":"success" , "message":"Succesfully got last user data", "data" : the_dict}))
            else:
                return HttpResponse(json.dumps({"state":"fail" ,"message":"No single checkin found for this ID"}))



def get_device_data_raw(request, device_id = None):
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
            return client_home(request,error="Henuz Multify Kaydiniz yok?")
        rec = CheckinRecord.objects.filter(multify=multify).order_by('-checkin_date')[:100]
        response = {"data" : [x.to_dict() for x in rec]}
        return HttpResponse(json.dumps(response))

@csrf_exempt
def push_welcomer(request):
    print request.POST
    return HttpResponse("Hola")