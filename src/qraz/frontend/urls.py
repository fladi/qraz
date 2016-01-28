#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import url, include

from rest_framework import routers

from . import (
    views,
)


router = routers.DefaultRouter()
router.register(r'synchronizations', views.SynchronizationViewSet, base_name = 'synchronization')
router.register(r'repositories', views.RepositoryViewSet, base_name = 'repository')
router.register(r'presentations', views.PresentationViewSet, base_name = 'presentation')

app_name = 'qraz'
urlpatterns = [
    url(
        r'^$',
        views.IndexView.as_view(),
        name='index'
    ),
    url(
        r'^presentations$',
        views.PresentationsView.as_view(),
        name='presentations'
    ),
    url(
        r'^repositories$',
        views.RepositoriesView.as_view(),
        name='repositories'
    ),
    url(
        r'^help$',
        views.HelpView.as_view(),
        name='help'
    ),
    url(
        r'^logout$',
        views.LogoutView.as_view(),
        name='logout'
    ),
    url(
        r'^api/',
        include(router.urls)
    ),
    url(
        r'^webhook/(?P<username>\w[\w_\-]+)/(?P<repository>[\w\-.]+)$',
        views.WebHookView.as_view(),
        name='webhook'
    ),
    url(
        r'^(?P<username>\w[\w_\-]+)/(?P<repository>\w[\w\-.]+)/(?P<presentation>\w[\w\-\._]+)/(?P<path>.*)?$',
        views.DownloadView.as_view(),
        name='download'
    )
]
