from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from tasks import models
from django.views.generic import ListView, DetailView, CreateView, View, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from tasks.mixins import UserIsOwnerMixin
from tasks.forms import TaskForm, TaskFilterForm, CommentForm
from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login


class TaskListView(LoginRequiredMixin, ListView):
    model = models.Task
    context_object_name = 'tasks'
    template_name = 'tasks/task_list.html'

    def get_queryset(self):
        queryset = super().get_queryset().filter(user=self.request.user)
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = TaskFilterForm(self.request.GET)
        return context
    
class TaskDetailView(LoginRequiredMixin, DetailView):
    model = models.Task
    context_object_name = 'task'
    template_name = 'tasks/task_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        return context

    def post(self, request, *args, **kwargs):
        comment_form = CommentForm(request.POST, request.FILES)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.user = request.user
            comment.task = self.get_object()
            comment.save()
            return redirect('tasks:task_detail', pk=comment.task.pk)
        else:
            pass

class TaskCreateView(LoginRequiredMixin, CreateView):
    model = models.Task
    template_name = 'tasks/task_form.html'
    form_class = TaskForm
    success_url = reverse_lazy('tasks:task_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class TaskUpdateView(LoginRequiredMixin, UserIsOwnerMixin, UpdateView):
    model = models.Task
    template_name = 'tasks/task_update_form.html'
    form_class = TaskForm
    success_url = reverse_lazy('tasks:task_list')


class TaskDeleteView(LoginRequiredMixin, UserIsOwnerMixin, DeleteView):
    model = models.Task
    template_name = 'tasks/task_delete_confirmation.html'
    success_url = reverse_lazy('tasks:task_list')


class CommentUpdateView(LoginRequiredMixin, UserIsOwnerMixin, UpdateView):
    model = models.Comment
    template_name = 'tasks/edit_comment.html'
    form_class = CommentForm
    success_url = reverse_lazy('tasks:task_detail') # Потрібно буде переписати get_success_url

    def get_success_url(self):
        return redirect('tasks:task_detail', pk=self.object.task.pk)


class CommentDeleteView(LoginRequiredMixin, UserIsOwnerMixin, DeleteView):
    model = models.Comment
    template_name = 'tasks/delete_comment.html'
    success_url = reverse_lazy('tasks:task_detail') # Потрібно буде переписати get_success_url

    def get_success_url(self):
        return redirect('tasks:task_detail', pk=self.object.task.pk)


class CustomLoginView(LoginView):
    template_name = 'tasks/login.html'
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('tasks:login')


class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'tasks/register.html'
    success_url = reverse_lazy('tasks:login')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('tasks:task_list')