from django.conf.urls import patterns, include, url
from django.contrib.auth.views import password_reset

urlpatterns = patterns('',
    url(r'^home/$', 'multify_app.views.index', name='index'),
    url(r'^submit_subscriber/$', 'multify_app.views.save_subscriber_record'),
    url(r'^client_login/$', 'multify_app.views.client_login', name='client_login'),
    url(r'^client_home/$', 'multify_app.views.client_home'),
    url(r'^multify_correct/$', 'multify_app.views.multify_correct'),
    url(r'^foursquare_token/$', 'multify_app.views.foursquare_token_generate'),
    url(r'^after_fsq_auth/$', 'multify_app.views.after_fsq_auth'),

    url(r'^logout/$', 'django.contrib.auth.views.logout' , {"next_page": 'client_login'}),
    url(r'^client_password_change/$', 'django.contrib.auth.views.password_change' , {'template_name': 'client/password_change.html' , 'post_change_redirect': '/client_home'}),

    url(r'^get_device_data/(?P<device_id>\w+)/$', 'multify_app.views.get_device_data'),
    url(r'^get_device_data/$', 'multify_app.views.get_device_data'),
    url(r'^get_device_data_raw/(?P<device_id>\w+)/$', 'multify_app.views.get_device_data_raw'),
    url(r'^get_checkins/$', 'multify_app.views.get_checkins'),

    url(r'^push_welcomer/$', 'multify_app.views.push_welcomer'),

    url(r'^order/$', 'multify_app.views.order_form'),
    url(r'^after_payment/$', 'multify_app.views.after_payment_page'),


    url(r'^$', 'multify_app.views.index', name='index'),


)

