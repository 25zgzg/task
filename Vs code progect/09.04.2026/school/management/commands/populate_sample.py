from django.core.management.base import BaseCommand

from school.models import Subject, Teacher, Class, Student, Schedule


class Command(BaseCommand):
    help = 'Populate sample subjects, classes, teachers, students and schedules'

    def handle(self, *args, **options):
        # clear minimal
        Subject.objects.all().delete()
        Teacher.objects.all().delete()
        Class.objects.all().delete()
        Student.objects.all().delete()
        Schedule.objects.all().delete()

        # Subjects
        maths = Subject.objects.create(name='Mathematics', description='Math')
        phys = Subject.objects.create(name='Physics', description='Physics')
        hist = Subject.objects.create(name='History', description='History')

        # Classes
        class_9a = Class.objects.create(name='9A', year_of_study=9)
        class_10b = Class.objects.create(name='10B', year_of_study=10)

        # Teachers
        t1 = Teacher.objects.create(first_name='Ivan', last_name='Petrov', subject=maths)
        t2 = Teacher.objects.create(first_name='Olena', last_name='Shevchenko', subject=phys)
        t3 = Teacher.objects.create(first_name='Maria', last_name='Kovalenko', subject=hist)

        # Students
        s1 = Student.objects.create(first_name='Andriy', last_name='Bondar', class_fk=class_9a)
        s2 = Student.objects.create(first_name='Kateryna', last_name='Ivanchuk', class_fk=class_10b)

        # Create a sample weekly schedule (Mon-Fri, hours 1-5)
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        for i, day in enumerate(days, start=1):
            Schedule.objects.create(day_of_week=day, hour_start=8 + (i % 5), subject=maths, class_fk=class_9a, teacher=t1)
            Schedule.objects.create(day_of_week=day, hour_start=9 + (i % 5), subject=phys, class_fk=class_9a, teacher=t2)
            Schedule.objects.create(day_of_week=day, hour_start=10 + (i % 5), subject=hist, class_fk=class_10b, teacher=t3)

        self.stdout.write(self.style.SUCCESS('Sample data populated'))
