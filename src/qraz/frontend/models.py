#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import string

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.fields import (
    ModificationDateTimeField,
)
from django_fsm import (
    FSMField,
    transition,
)
from github import (
    Github,
    GithubException,
)
from markupfield.fields import MarkupField
from purl import URL
from social.apps.django_app.default.models import UserSocialAuth

logger = logging.getLogger(__name__)


def get_secret():
    return ''.join(get_random_string(16, string.ascii_letters + string.digits))


class Repository(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    github = models.PositiveIntegerField(
        verbose_name=_('Github repository ID')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    name = models.CharField(
        max_length=256,
        verbose_name=_('Repository name')
    )
    state = FSMField(
        default='inactive',
        protected=True
    )
    modified = ModificationDateTimeField(
        verbose_name=_('Last modified')
    )
    comment = MarkupField(
        blank=True,
        null=True,
        default_markup_type='ReST',
        verbose_name=_('Comment')
    )
    secret = models.CharField(
        max_length=16,
        default=get_secret,
        verbose_name=_('Shared secret for Github webhooks')
    )
    hook = models.PositiveIntegerField(
        null=True,
        verbose_name=_('ID of Github webhook')
    )
    fork = models.BooleanField(
        default=False
    )

    class Meta(object):
        ordering = [
            'name',
        ]

    @transition(field=state, source='inactive', target='active')
    def activate(self, *args, **kwargs):
        """
        Transition: inactive -> active

        Set github webhook and activate all Presentations.
        """
        try:
            provider = self.user.social_auth.get(provider='github')
        except UserSocialAuth.DoesNotExists:
            logger.error('No social auth provider for Github found on user')
            return
        github = Github(provider.access_token)
        try:
            repo = github.get_user().get_repo(self.name)
        except GithubException:
            logger.error('Could not find repository')
            return
        url = URL(
            scheme='http',
            host=self.site.domain,
            path=reverse('qraz:webhook', kwargs={'username': self.user.username, 'repository': self.name})
        )
        try:
            hook = repo.create_hook(
                'web',
                {
                    'url': url.as_string(),
                    'content_type': 'json',
                    'secret': self.secret,
                },
                events=['push'],
                active=True
            )
        except GithubException as excp:
            logger.error('Could not create webhook: %s', excp)
            return
        self.hook = hook.id

    @transition(field=state, source='*', target='inactive')
    def deactivate(self, *args, **kwargs):
        """
        This function may contain side-effects,
        like updating caches, notifying users, etc.
        The return value will be discarded.
        """
        if self.hook:
            try:
                provider = self.user.social_auth.get(provider='github')
            except UserSocialAuth.DoesNotExists:
                logger.error('No social auth provider for Github found on user')
                raise
            github = Github(provider.access_token)
            try:
                repo = github.get_user().get_repo(self.name)
            except GithubException:
                logger.error('Could not find repository')
                raise
            try:
                hook = repo.get_hook(self.hook)
                hook.delete()
            except GithubException as excp:
                logger.error('Could not remove webhook: %s', excp)
        self.hook = None


class Presentation(models.Model):
    repository = models.ForeignKey(
        Repository
    )
    name = models.CharField(
        max_length=128
    )
    path = models.TextField()
    modified = ModificationDateTimeField(
        verbose_name=_('Last modified')
    )

    @property
    def fullname(self):
        return '{self.repository.name}/{self.name}'.format(self=self)

    @property
    def url(self):
        kwargs = {
            'username': self.repository.user.username,
            'repository': self.repository.name,
            'presentation': self.name,
        }
        url = URL(
            scheme='http',
            host=self.repository.site.domain,
            path=reverse('qraz:download', kwargs=kwargs)
        )
        return url.as_string()
