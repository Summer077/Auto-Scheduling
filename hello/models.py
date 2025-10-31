from django.db import models
from django.contrib.auth.models import User

class Curriculum(models.Model):
    name = models.CharField(max_length=100)
    year = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-year']
        unique_together = ['name', 'year']
    
    def __str__(self):
        return f"{self.name} ({self.year})"

class Course(models.Model):
    YEAR_CHOICES = [
        (1, '1st Year'),
        (2, '2nd Year'),
        (3, '3rd Year'),
        (4, '4th Year'),
    ]
    
    SEMESTER_CHOICES = [
        (1, '1st Semester'),
        (2, '2nd Semester'),
    ]
    
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='courses')
    course_code = models.CharField(max_length=20)
    descriptive_title = models.CharField(max_length=200)
    laboratory_hours = models.IntegerField(default=0)
    lecture_hours = models.IntegerField(default=0)
    credit_units = models.IntegerField(default=0)
    year_level = models.IntegerField(choices=YEAR_CHOICES)
    semester = models.IntegerField(choices=SEMESTER_CHOICES)
    color = models.CharField(max_length=7, default='#FFA726')  # Hex color for schedule display
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['year_level', 'semester', 'course_code']
        unique_together = ['curriculum', 'course_code']
    
    def __str__(self):
        return f"{self.course_code} - {self.descriptive_title}"
    
    def get_year_semester_display(self):
        year = dict(self.YEAR_CHOICES)[self.year_level]
        semester = dict(self.SEMESTER_CHOICES)[self.semester]
        return f"{year}, {semester}"

class Faculty(models.Model):
    """Model for faculty members"""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name_plural = 'Faculty'
    
    def __str__(self):
        return f"{self.last_name}, {self.first_name}"

class Section(models.Model):
    """Model for class sections"""
    name = models.CharField(max_length=50)  # e.g., "CPE3LS1"
    year_level = models.IntegerField(choices=Course.YEAR_CHOICES)
    semester = models.IntegerField(choices=Course.SEMESTER_CHOICES)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='sections')
    max_students = models.IntegerField(default=40)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['year_level', 'semester', 'name']
        unique_together = ['curriculum', 'name']
    
    def __str__(self):
        return self.name

class Room(models.Model):
    """Model for classrooms"""
    name = models.CharField(max_length=50, unique=True)  # e.g., "A-225"
    building = models.CharField(max_length=50, blank=True)
    capacity = models.IntegerField(default=40)
    room_type = models.CharField(max_length=50, blank=True)  # Lab, Lecture, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Schedule(models.Model):
    """Model for course schedules"""
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='schedules')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='schedules')
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='schedules')
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='schedules')
    day = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.CharField(max_length=5)  # Format: "HH:MM" (e.g., "8:30")
    end_time = models.CharField(max_length=5)    # Format: "HH:MM" (e.g., "10:30")
    duration = models.IntegerField(help_text="Duration in minutes")  # e.g., 120 for 2 hours
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['day', 'start_time']
    
    def __str__(self):
        day_name = dict(self.DAY_CHOICES)[self.day]
        return f"{self.course.course_code} - {day_name} {self.start_time}-{self.end_time}"

class Activity(models.Model):
    """Model for tracking user activities"""
    ACTION_CHOICES = [
        ('add', 'Added'),
        ('edit', 'Edited'),
        ('delete', 'Deleted'),
    ]
    
    ENTITY_CHOICES = [
        ('course', 'Course'),
        ('curriculum', 'Curriculum'),
        ('faculty', 'Faculty'),
        ('section', 'Section'),
        ('schedule', 'Schedule'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    entity_type = models.CharField(max_length=20, choices=ENTITY_CHOICES)
    entity_name = models.CharField(max_length=200)  # Name/code of the entity
    message = models.TextField()  # Full activity message
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Activities'
    
    def __str__(self):
        return f"{self.action} {self.entity_type}: {self.entity_name}"