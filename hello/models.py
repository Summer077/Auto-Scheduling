from django.db import models
from django.contrib.auth.models import User
import random
import re
from django.core.exceptions import ValidationError

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
    
    # Predefined color palette for courses
    COLOR_PALETTE = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DFE6E9', '#74B9FF', '#A29BFE', '#FD79A8', '#FDCB6E',
        '#6C5CE7', '#00B894', '#E17055', '#0984E3', '#00CEC9',
        '#B2BEC3', '#FF7675', '#55EFC4', '#FAB1A0', '#A29BFE',
    ]
    
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='courses')
    course_code = models.CharField(max_length=20)
    descriptive_title = models.CharField(max_length=200)
    laboratory_hours = models.IntegerField(default=0)
    lecture_hours = models.IntegerField(default=0)
    credit_units = models.IntegerField(default=0)
    year_level = models.IntegerField(choices=YEAR_CHOICES)
    semester = models.IntegerField(choices=SEMESTER_CHOICES)
    color = models.CharField(max_length=7, default='#FFA726')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['year_level', 'semester', 'course_code']
        unique_together = ['curriculum', 'course_code']
    
    def save(self, *args, **kwargs):
        """Auto-assign a unique color if not set"""
        if not self.color or self.color == '#FFA726':
            existing_colors = Course.objects.filter(
                curriculum=self.curriculum
            ).exclude(id=self.id).values_list('color', flat=True)
            
            available_colors = [c for c in self.COLOR_PALETTE if c not in existing_colors]
            
            if available_colors:
                self.color = random.choice(available_colors)
            else:
                self.color = random.choice(self.COLOR_PALETTE)
        
        super().save(*args, **kwargs)
    
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
    
    @property
    def total_units(self):
        """Automatically calculate total credit units from assigned schedules."""
        schedules = self.schedules.select_related('course')
        total = sum(s.course.credit_units for s in schedules)
        return total

class Section(models.Model):
    """Model for class sections with naming convention CPE[year][semester]S[number]"""
    name = models.CharField(max_length=50)
    year_level = models.IntegerField(choices=Course.YEAR_CHOICES)
    semester = models.IntegerField(choices=Course.SEMESTER_CHOICES)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='sections')
    max_students = models.IntegerField(default=40)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['year_level', 'semester', 'name']
        unique_together = ['curriculum', 'name']
    
    def clean(self):
        """Validate section name format: CPE[year][semester]S[number]"""
        super().clean()
        
        pattern = r'^([A-Z]+)(\d)(\d)S(\d+)$'
        match = re.match(pattern, self.name)
        
        if not match:
            raise ValidationError({
                'name': 'Section name must follow format: CPE[year][semester]S[number]. Example: CPE11S1'
            })
        
        program, year_digit, sem_digit, section_num = match.groups()
        name_year = int(year_digit)
        name_sem = int(sem_digit)
        
        if name_year != self.year_level:
            raise ValidationError({
                'name': f'Section name year ({name_year}) must match year level ({self.year_level})'
            })
        
        if name_sem != self.semester:
            raise ValidationError({
                'name': f'Section name semester ({name_sem}) must match semester ({self.semester})'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class Room(models.Model):
    """Model for classrooms"""
    name = models.CharField(max_length=50, unique=True)
    building = models.CharField(max_length=50, blank=True)
    capacity = models.IntegerField(default=40)
    room_type = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Schedule(models.Model):
    """Model for course schedules with validation"""
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
    start_time = models.CharField(max_length=5)
    end_time = models.CharField(max_length=5)
    duration = models.IntegerField(default=0, help_text="Duration in minutes")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['day', 'start_time']
    
    def clean(self):
        """Validate course matches section's year/semester"""
        super().clean()
        
        if self.course.year_level != self.section.year_level:
            raise ValidationError(
                f'Cannot add {self.course.course_code} (Year {self.course.year_level}) '
                f'to {self.section.name} (Year {self.section.year_level})'
            )
        
        if self.course.semester != self.section.semester:
            raise ValidationError(
                f'Cannot add {self.course.course_code} (Semester {self.course.semester}) '
                f'to {self.section.name} (Semester {self.section.semester})'
            )
        
        if self.course.curriculum != self.section.curriculum:
            raise ValidationError(
                f'{self.course.course_code} curriculum does not match {self.section.name} curriculum'
            )
    
    def save(self, *args, **kwargs):
        """Calculate duration and validate"""
        if self.start_time and self.end_time:
            start_hour, start_min = map(int, self.start_time.split(':'))
            end_hour, end_min = map(int, self.end_time.split(':'))
            self.duration = (end_hour * 60 + end_min) - (start_hour * 60 + start_min)

        if self.faculty:
            current_units = sum(
                s.course.credit_units for s in self.faculty.schedules.exclude(pk=self.pk)
            )
            if current_units + self.course.credit_units > 25:
                raise ValidationError(
                    f"{self.faculty.first_name} {self.faculty.last_name} would exceed 25-unit limit"
                )
        
        self.full_clean()
        super().save(*args, **kwargs)
    
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
    entity_name = models.CharField(max_length=200)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Activities'
    
    def __str__(self):
        return f"{self.action} {self.entity_type}: {self.entity_name}"