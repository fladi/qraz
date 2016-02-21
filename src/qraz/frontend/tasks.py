#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import glob
import os
import shutil
import subprocess
import tempfile

import pygit2
import yaml

from django.conf import settings
from django.utils import timezone

from celery import Task
from celery.utils.log import get_task_logger
from github import (
    Github,
    GithubException,
)
from social.apps.django_app.default.models import UserSocialAuth

from .models import (
    Repository,
    Presentation,
)

logger = get_task_logger(__name__)


class SynchronizationTask(Task):
    ignore_result = False

    def run(self, user, site, *args, **kwargs):
        try:
            provider = user.social_auth.get(provider='github')
        except UserSocialAuth.DoesNotExists:
            logger.error('No social auth provider for Github found on user')
            return
        github = Github(provider.access_token)
        prior = timezone.now()
        repos = list(github.get_user().get_repos())
        logger.info('Synchronizing %d repositories for user %s', len(repos), user.username)
        for i, repo in enumerate(repos):
            logger.debug('Processing repository: %s (%d/%d)', repo.name, i, len(repos))
            if not self.request.called_directly:
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i+1,
                        'total': len(repos)
                    }
                )
            instance, created = Repository.objects.get_or_create(
                site=site,
                user=user,
                github=repo.id,
                defaults={
                    'name': repo.name,
                    'fork': repo.fork,
                }
            )
            if not created:
                logger.debug('Updating repository instance: %s', instance.name)
                instance.save()
            else:
                logger.debug('Creating repository instance: %s', instance.name)
        logger.info('Removing old repositories')
        for stale in Repository.objects.filter(site=site, user=user, modified__lt=prior):
            stale.deactivate()
            stale.delete()


class ActivationTask(Task):
    ignore_result = False

    def run(self, repository, *args, **kwargs):
        try:
            repository.activate()
        except:
            logger.warn('Repository activation failed: %s', repository.name)
            return False
        logger.debug('Repository activated: %s', repository.name)
        repository.save()
        return True


class BuildTask(Task):
    ignore_result = True

    def build(self, copy, presentation, assets, *args, **kwargs):
        subprocess.call(
            [
                '/usr/bin/hovercraft',
                os.path.join(copy, presentation.path),
                os.path.join(
                    settings.HOVERCRAFT_ROOT,
                    str(presentation.pk)
                )
            ]
        )
        for asset in assets:
            asset_glob = os.path.realpath(
                os.path.abspath(os.path.join(copy, asset))
            )
            if not os.path.commonpath([copy, asset_glob]).startswith(copy):
                logger.warn("Malicious asset: %s", asset)
                continue
            for asset_source in glob.glob(asset_glob, recursive=True):
                asset_target = os.path.join(
                    settings.HOVERCRAFT_ROOT,
                    str(presentation.pk),
                    os.path.relpath(asset_source, copy)
                )
                if os.path.isdir(asset_source):
                    for root, dirs, files in os.walk(asset_source):
                        rel_path = os.path.relpath(root, asset_source)
                        dest_dir = os.path.join(asset_target, rel_path)
                        if not os.path.isdir(dest_dir):
                            os.makedirs(dest_dir)
                        for each_file in files:
                            dest_path = os.path.join(dest_dir, each_file)
                            shutil.copyfile(os.path.join(root, each_file), dest_path)
                else:
                    shutil.copyfile(asset_source, asset_target)

    def run(self, repository, *args, **kwargs):
        try:
            provider = repository.user.social_auth.get(provider='github')
        except UserSocialAuth.DoesNotExists:
            logger.error('No social auth provider for Github found on user')
            return False
        github = Github(provider.access_token)
        try:
            repo = github.get_user().get_repo(repository.name)
        except GithubException:
            logger.error('Could not find repository')
            return False
        prior = timezone.now()
        with tempfile.TemporaryDirectory() as copy:
            pygit2.clone_repository(repo.git_url, copy)
            config_file = os.path.join(copy, '.hovercraft.yml')
            if os.access(config_file, os.R_OK):
                with io.open(config_file, 'r', encoding='utf-8') as stream:
                    config = yaml.load(stream)
                for presentation in repository.presentation_set.all():
                    shutil.rmtree(
                        os.path.join(
                            settings.HOVERCRAFT_ROOT,
                            str(presentation.pk)
                        ),
                        ignore_errors=True
                    )
                for presentation, data in config.items():
                    source = data.get('source', '{}.rst'.format(presentation,))
                    source_path = os.path.realpath(os.path.abspath(os.path.join(copy, source)))
                    if not os.path.isfile(source_path):
                        logger.warn('Source not found: %s', source)
                        continue
                    if not os.path.commonpath([copy, source_path]).startswith(copy):
                        logger.warn('Malicious source: %s', source)
                        continue
                    instance, created = Presentation.objects.get_or_create(
                        repository=repository,
                        name=presentation,
                        defaults={
                            'path': source,
                        }
                    )
                    if not created:
                        instance.save()
                    self.build(copy, instance, data.get('assets', []))
            Presentation.objects.filter(repository=repository, modified__lt=prior).delete()

