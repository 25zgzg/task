from django.urls import path
from . import views

app_name = 'school'

urlpatterns = [
    path('subjects/', views.SubjectCreateView.as_view(), name='subjects'),
    path('teachers/', views.TeacherCreateView.as_view(), name='teachers'),
    path('classes/', views.ClassCreateView.as_view(), name='classes_create'),
    path('classes/list/', views.ClassListView.as_view(), name='classes_list'),
    path('students/', views.StudentCreateView.as_view(), name='students'),
    path('schedules/', views.ScheduleCreateView.as_view(), name='schedules'),
    path('schedules/new/<int:class_id>/', views.ScheduleCreateView.as_view(), name='schedule_new'),
    path('schedules/<int:pk>/edit/', views.ScheduleUpdateView.as_view(), name='schedule_edit'),
    path('schedules/<int:pk>/delete/', views.ScheduleDeleteView.as_view(), name='schedule_delete'),
    path('grades/', views.GradeCreateView.as_view(), name='grades'),
    path('classes/<int:class_id>/schedule/', views.ClassScheduleView.as_view(), name='class_schedule'),
    path('classes/<int:class_id>/timetable/', views.class_timetable_view, name='timetable'),
]
