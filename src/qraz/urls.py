#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = [
    url(
        r'^api-auth/',
        include(
            'rest_framework.urls',
            namespace='rest_framework'
        )
    ),
    url(
        r'^oauth2/',
        include(
            'oauth2_provider.urls',
            namespace='oauth2_provider'
        )
    ),
    url(
        r'^admin/',
        include(admin.site.urls)
    ),
    url(
        r'^',
        include('social.apps.django_app.urls', namespace='social')
    ),
    url(
        r'^',
        include('qraz.frontend.urls', namespace='qraz')
    ),
]
