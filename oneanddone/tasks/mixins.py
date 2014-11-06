# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.shortcuts import redirect
from tower import ugettext as _

from oneanddone.tasks.models import Task, TaskAttempt


class APIOnlyCreatorMayDeleteMixin(object):
    def pre_delete(self, obj):
        if obj.creator != self.request.user:
            raise PermissionDenied()


class APIRecordCreatorMixin(object):
    def pre_save(self, obj):
        obj.creator = self.request.user


class GetUserAttemptMixin(object):
    """
    Retrieve a user attempt and add it to the view's self scope
    for later use.
    """
    def dispatch(self, request, *args, **kwargs):
        self.attempt = get_object_or_404(TaskAttempt, pk=kwargs['pk'], user=request.user,
                                         state__in=[TaskAttempt.FINISHED, TaskAttempt.ABANDONED])
        return super(GetUserAttemptMixin, self).dispatch(request, *args, **kwargs)


class HideNonRepeatableTaskMixin(object):
    """
    Do not allow access to a non-repeatable task that is not available to the user.
    """
    def get_object(self, queryset=None):
        task = super(HideNonRepeatableTaskMixin, self).get_object(queryset)
        if not task.is_available_to_user(self.request.user):
            raise Http404('Task unavailable.')
        return task


class TaskMustBeAvailableMixin(object):
    """
    Only allow published tasks to be listed, by filtering the
    queryset.
    """
    allow_expired_tasks = False

    def get_queryset(self):
        queryset = super(TaskMustBeAvailableMixin, self).get_queryset()
        return queryset.filter(Task.is_available_filter(allow_expired=self.allow_expired_tasks))
        
        
class SetExecutionTime(object):
    def form_valid(self, form):
        self.object = form.save(self.request.user, commit=False)
        admin_time = form.cleaned_data['admin_time']
        if admin_time:
            self.object.execution_time = admin_time
            self.object.save()
        form.save(self.request.user)
        
        messages.success(self.request, _('Your task has been updated.'))
        return redirect('tasks.list')
