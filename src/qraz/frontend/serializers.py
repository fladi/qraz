#!/usr/bin/env python
# -*- coding: utf-8 -*-

from rest_framework import serializers


from . import models


class RepositorySerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.Repository
        fields = ('id', 'name', 'state')


class PresentationSerializer(serializers.HyperlinkedModelSerializer):
    fullname = serializers.ReadOnlyField()
    url = serializers.ReadOnlyField()

    class Meta:
        model = models.Presentation
        fields = ('id', 'fullname', 'url')
