import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('stage', 'Stage'),
        ('unit', 'Unit'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    
    username = None  # Remove username field
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'  # Set email as username
    REQUIRED_FIELDS = []  # Remove 'username' from required fields


class Sector(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'role': 'admin'})

    def __str__(self):
        return self.name


class Unit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name='units')
    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'role': 'unit'})

    def __str__(self):
        return self.name

class Stage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name='stages')
    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'role': 'stage'})

    def __str__(self):
        return self.name


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Competition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return self.name



class Result(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.OneToOneField(Competition, on_delete=models.CASCADE, related_name='result')
    image = models.ImageField(upload_to='results/')

    def __str__(self):
        return f"Result - {self.competition.name}"


class News(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ImageField(upload_to='news/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"News - {self.id}"


class Gallery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ImageField(upload_to='gallery/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Gallery - {self.id}"

class ScheduledCompetition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE)
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name='scheduled_competitions')
    reporting_time = models.DateTimeField()
    date = models.DateField(null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('reporting', 'Reporting'),
        ('ongoing', 'Ongoing'),
        ('finished', 'Finished'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')

    class Meta:
        unique_together = ('competition', 'sector')
    
    def clean(self):
        super().clean()
        if self.date and self.stage:
            # Look for overlapping scheduled competitions
            overlapping = ScheduledCompetition.objects.filter(
                stage=self.stage,
                date=self.date,
            ).exclude(id=self.id).filter(
                Q(start_time__lt=self.end_time) & Q(end_time__gt=self.start_time)
            )

            if overlapping.exists():
                raise ValidationError(
                    _("A competition is already scheduled in this stage and date within the specified time range.")
                )
    # Enforce only one 'ongoing' per stage per date
        if self.status == 'ongoing':
            exists = ScheduledCompetition.objects.filter(
                stage=self.stage,
                date=self.date,
                status='ongoing'
            ).exclude(id=self.id).exists()
            if exists:
                raise ValidationError(_("Only one ongoing competition is allowed per stage per date."))

        # Enforce only one 'reporting' per stage per date
        if self.status == 'reporting':
            exists = ScheduledCompetition.objects.filter(
                stage=self.stage,
                date=self.date,
                status='reporting'
            ).exclude(id=self.id).exists()
            if exists:
                raise ValidationError(_("Only one reporting competition is allowed per stage per date."))
            
    def save(self, *args, **kwargs):
        self.full_clean()  # Triggers the clean method
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.competition.name} - {self.sector.name}"


class ParticipantPresent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scheduled_competition = models.ForeignKey(ScheduledCompetition, on_delete=models.CASCADE, related_name='participants')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    participant_1_present = models.BooleanField(default=False)
    participant_2_present = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('scheduled_competition', 'unit')
        verbose_name = 'Participant Present'
        verbose_name_plural = 'Participants Present'

    def __str__(self):
        return f"{self.scheduled_competition.competition.name} - {self.unit.name}"


# Signal to automatically create ParticipantPresent objects when ScheduledCompetition is created
@receiver(post_save, sender=ScheduledCompetition)
def create_participant_present_records(sender, instance, created, **kwargs):
    """
    Automatically create ParticipantPresent records for all units in the sector
    when a new ScheduledCompetition is created.
    """
    if created:
        # Get all units in the sector of the scheduled competition
        units = Unit.objects.filter(sector=instance.sector)
        
        # Create ParticipantPresent records for each unit
        participant_records = []
        for unit in units:
            participant_records.append(
                ParticipantPresent(
                    scheduled_competition=instance,
                    unit=unit,
                    participant_1_present=False,
                    participant_2_present=False
                )
            )
        
        # Bulk create for better performance
        ParticipantPresent.objects.bulk_create(participant_records)