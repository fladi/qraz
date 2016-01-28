#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page, never_cache

from rest_framework.decorators import detail_route
from rest_framework.response import Response

from django_fsm import FSMField


def get_state_field_viewset_method(methods, **kwargs):
    '''
    Create a viewset method for the provided FSM `field` by adding all its
    transition methods as HTTP methods.
    '''

    @detail_route(methods=[name.lower() for name in methods], **kwargs)
    def inner_func(self, request, pk=None):
        object = self.get_object()
        transition_method = getattr(object, request.method.lower())

        transition_method(by=self.request.user)

        if self.save_after_transition:
            object.save()

        serializer = self.get_serializer(object)
        return Response(serializer.data)

    return inner_func


def get_viewset_transition_action_mixin(model, **kwargs):
    '''
    Find all FSM fields defined on `model`, then create a corresponding
    viewset action method for each and apply it to `Mixin`. Finally, return
    `Mixin`
    '''
    methods = set()

    class MetaTransitionMixin(type):

        def __init__(cls, name, bases, dct):
            # See if one of our base classes is an instance of MetaTransitionMixin metaclass. If so, it should be our mixin.
            if any(isinstance(base, MetaTransitionMixin) for base in bases):
                base_methods = set(next((getattr(base, 'http_method_names') for base in bases if hasattr(base, 'http_method_names')), list()))
                base_methods.update(methods)
                setattr(cls, 'http_method_names', list(base_methods))
            super(MetaTransitionMixin, cls).__init__(name, bases, dct)


    class TransitionMixin(metaclass=MetaTransitionMixin):
        save_after_transition = True


    for field in model._meta.get_fields():
        if isinstance(field, FSMField):
            transitions = [method.name.lower() for method in field.get_all_transitions(model)]
            setattr(
                TransitionMixin,
                field.name,
                get_state_field_viewset_method(transitions, **kwargs)
            )
            methods.update(transitions)

        #setattr(
        #    TransitionMixin,
        #    'http_method_names',
        #    list(methods)
        #)

    return TransitionMixin


class CacheMixin(object):
    cache_timeout = 60

    def get_cache_timeout(self):
        return self.cache_timeout

    def dispatch(self, *args, **kwargs):
        response = super(CacheMixin, self).dispatch
        decorator = cache_page(self.get_cache_timeout())
        return decorator(response)(*args, **kwargs)

class NeverCacheMixin(object):

    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super(NeverCacheMixin, self).dispatch(*args, **kwargs)
