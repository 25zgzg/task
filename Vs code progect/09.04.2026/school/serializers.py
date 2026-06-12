from rest_framework import serializers
from .models import Subject, Teacher, Class, Student, Schedule, Grade


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'description']

    def validate_name(self, value):
        if Subject.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError('Предмет з такою назвою вже існує')
        return value


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ['id', 'first_name', 'last_name', 'subject']

    def validate(self, attrs):
        subj = attrs.get('subject')
        if subj is None:
            return attrs
        return attrs


class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ['id', 'name', 'year_of_study']

    def validate_name(self, value):
        if Class.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError('Клас з такою назвою вже існує')
        return value


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'first_name', 'last_name', 'class_fk']


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ['id', 'day_of_week', 'hour_start', 'subject', 'class_fk', 'teacher']


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ['id', 'student', 'subject', 'grade_value', 'date']
