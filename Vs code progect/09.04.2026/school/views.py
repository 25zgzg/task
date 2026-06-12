from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import ListView

from .forms import ScheduleForm

from .models import Subject, Teacher, Class, Student, Schedule, Grade
from .serializers import (
    SubjectSerializer, TeacherSerializer, ClassSerializer,
    StudentSerializer, ScheduleSerializer, GradeSerializer
)


class SubjectCreateView(APIView):
    def post(self, request):
        serializer = SubjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TeacherCreateView(APIView):
    def post(self, request):
        serializer = TeacherSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subj = serializer.validated_data.get('subject')
        if subj is None:
            return Response({'detail': 'Предмет не знайдено'}, status=status.HTTP_404_NOT_FOUND)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ClassCreateView(APIView):
    def post(self, request):
        serializer = ClassSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class StudentCreateView(APIView):
    def post(self, request):
        serializer = StudentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cls = serializer.validated_data.get('class_fk')
        if not cls:
            return Response({'detail': 'Клас не знайдено'}, status=status.HTTP_404_NOT_FOUND)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ScheduleCreateView(APIView):
    def post(self, request):
        serializer = ScheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        class_id = request.query_params.get('class_id')
        day = request.query_params.get('day_of_week')
        qs = Schedule.objects.all()
        if class_id:
            qs = qs.filter(class_fk_id=class_id)
        if day:
            qs = qs.filter(day_of_week__iexact=day)
        serializer = ScheduleSerializer(qs, many=True)
        return Response(serializer.data)


class GradeCreateView(APIView):
    def post(self, request):
        serializer = GradeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ClassScheduleView(APIView):
    def get(self, request, class_id: int):
        day = request.query_params.get('day_of_week')
        qs = Schedule.objects.filter(class_fk_id=class_id)
        if day:
            qs = qs.filter(day_of_week__iexact=day)
        serializer = ScheduleSerializer(qs, many=True)
        return Response(serializer.data)


def class_timetable_view(request, class_id: int):
    """Render a simple weekly timetable for a class (Mon-Fri, hours 1-8)."""
    class_obj = get_object_or_404(Class, pk=class_id)
    # Hours to display (you can adjust range)
    hours = list(range(1, 9))
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    # Build a mapping (day -> hour -> schedule entry)
    entries = Schedule.objects.filter(class_fk=class_obj)
    table = {day: {h: None for h in hours} for day in days}
    for e in entries:
        h = e.hour_start if e.hour_start in hours else None
        if h and e.day_of_week in table:
            table[e.day_of_week][h] = e

    # Build rows for easier template rendering
    rows = []
    for h in hours:
        row = {'hour': h, 'cells': [table[day].get(h) for day in days]}
        rows.append(row)

    context = {
        'class_obj': class_obj,
        'hours': hours,
        'days': days,
        'rows': rows,
    }
    return render(request, 'school/timetable.html', context)


class ClassListView(ListView):
    model = Class
    template_name = 'school/class_list.html'
    context_object_name = 'classes'


class ScheduleCreateView(View):
    def get(self, request, class_id=None):
        initial = {}
        if class_id:
            initial['class_fk'] = class_id
        form = ScheduleForm(initial=initial)
        return render(request, 'school/schedule_form.html', {'form': form})

    def post(self, request, class_id=None):
        form = ScheduleForm(request.POST)
        if form.is_valid():
            sched = form.save()
            return redirect(reverse('school:timetable', args=[sched.class_fk_id]))
        return render(request, 'school/schedule_form.html', {'form': form})


class ScheduleUpdateView(View):
    def get(self, request, pk):
        sched = get_object_or_404(Schedule, pk=pk)
        form = ScheduleForm(instance=sched)
        return render(request, 'school/schedule_form.html', {'form': form, 'object': sched})

    def post(self, request, pk):
        sched = get_object_or_404(Schedule, pk=pk)
        form = ScheduleForm(request.POST, instance=sched)
        if form.is_valid():
            form.save()
            return redirect(reverse('school:timetable', args=[sched.class_fk_id]))
        return render(request, 'school/schedule_form.html', {'form': form, 'object': sched})


class ScheduleDeleteView(View):
    def get(self, request, pk):
        sched = get_object_or_404(Schedule, pk=pk)
        return render(request, 'school/schedule_confirm_delete.html', {'object': sched})

    def post(self, request, pk):
        sched = get_object_or_404(Schedule, pk=pk)
        class_id = sched.class_fk_id
        sched.delete()
        return redirect(reverse('school:timetable', args=[class_id]))
