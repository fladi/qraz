#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
import hmac
import os

from django.conf import settings
from django.contrib.auth import logout
from django.http import (
    HttpResponseBadRequest,
    HttpResponseNotFound,
)
from django.views.generic import (
    View,
    TemplateView,
    RedirectView,
)
from django.core.urlresolvers import reverse_lazy as reverse

from braces.views import (
    LoginRequiredMixin,
    CsrfExemptMixin,
    JsonRequestResponseMixin
)
from django_downloadview import PathDownloadView
from rest_framework.response import Response
from rest_framework.viewsets import (
    ViewSet,
    ReadOnlyModelViewSet,
    ModelViewSet,
)

from . import (
    models,
    serializers,
    tasks,
)
from .mixins import (
    get_viewset_transition_action_mixin,
    CacheMixin,
    NeverCacheMixin
)


class LogoutView(RedirectView):
    url = reverse('qraz:index')

    def get(self, request, *args, **kwargs):
        logout(request)
        response = super(LogoutView, self).get(request, *args, **kwargs)
        return response


class NotFoundView(RedirectView):
    url = reverse('qraz:index')


class IndexView(TemplateView):
    template_name = 'qraz/index.html'


class PresentationsView(LoginRequiredMixin, TemplateView):
    template_name = 'qraz/presentations.html'


class RepositoriesView(LoginRequiredMixin, TemplateView):
    template_name = 'qraz/repositories.html'


class HelpView(TemplateView):
    template_name = 'qraz/help.html'


class WebHookView(CsrfExemptMixin, JsonRequestResponseMixin, View):
    require_json = True

    def post(self, request, username, repository):
        if 'HTTP_X_HUB_SIGNATURE' not in request.META:
            return HttpResponseBadRequest('No X-GITHUB-EVENT header found')
        if 'HTTP_X_GITHUB_EVENT' not in request.META:
            return HttpResponseBadRequest('No X-GITHUB-EVENT header found')
        try:
            repo = models.Repository.objects.get(name=repository, user__username=username)
        except models.Repository.DoesNotExist:
            return HttpResponseNotFound()
        sha_name, signature = request.META['HTTP_X_HUB_SIGNATURE'].split('=')
        if sha_name != 'sha1':
            return HttpResponseBadRequest('Invalid X-HUB-SIGNATURE digest mode found')
        mac = hmac.new(
            repo.secret.encode('utf-8'),
            msg=request.body,
            digestmod=hashlib.sha1
        )
        if not hmac.compare_digest(mac.hexdigest(), signature):
            return HttpResponseBadRequest('Invalid X-HUB-SIGNATURE header found')
        event = 'on_{}'.format(request.META['HTTP_X_GITHUB_EVENT'])
        if not hasattr(self, event):
            return HttpResponseBadRequest('Invalid X-GITHUB-EVENT header found')
        handler = getattr(self, event)
        response = handler(repo)
        return self.render_json_response(response)

    def on_ping(self, repository):
        repository.hook = self.request_json['hook_id']
        repository.save()
        return {}

    def on_push(self, repository):
        task = tasks.BuildTask().delay(repository)
        return {
            'uuid': repository.id,
            'state': repository.state,
            'task': task.id,
        }


class DownloadView(CacheMixin, PathDownloadView):
    attachment = False

    def get_path(self):
        """Return path inside fixtures directory."""
        presentation = models.Presentation.objects.get(
            name=self.kwargs['presentation'],
            repository__name=self.kwargs['repository'],
            repository__user__username=self.kwargs['username'],
            repository__site=self.request.site
        )
        # Get path from URL resolvers or as_view kwarg.
        relative_path = super(DownloadView, self).get_path()
        # Make it absolute.
        if not relative_path:
            relative_path = 'index.html'
        absolute_path = os.path.join(
            settings.HOVERCRAFT_ROOT,
            str(presentation.pk),
            relative_path
        )
        return absolute_path


class RepositoryViewSet(get_viewset_transition_action_mixin(models.Repository), ReadOnlyModelViewSet):
    """
    API endpoint that allows repositories to be viewed.
    """
    serializer_class = serializers.RepositorySerializer
    permission_classes = []

    def get_queryset(self):
        """
        This view should return a list of all the repositories
        for the currently authenticated user.
        """
        return models.Repository.objects.filter(site=self.request.site, user=self.request.user)


class PresentationViewSet(ReadOnlyModelViewSet):
    """
    API endpoint that allows presentations to be viewed.
    """
    serializer_class = serializers.PresentationSerializer
    permission_classes = []

    def get_queryset(self):
        """
        This view should return a list of all the presentations
        for the currently authenticated user.
        """
        return models.Presentation.objects.filter(repository__site=self.request.site, repository__user=self.request.user)


class SynchronizationViewSet(NeverCacheMixin, ViewSet):
    permission_classes = []

    def create(self, request):
        task = tasks.SynchronizationTask().delay(request.user, request.site)
        return Response({
            'id': task.id,
            'state': task.state,
            'result': task.result,
        })

    def retrieve(self, request, pk):
        task = tasks.SynchronizationTask().AsyncResult(pk)
        return Response({
            'id': task.id,
            'state': task.state,
            'result': task.result,
        })


handle404 = NotFoundView.as_view()
