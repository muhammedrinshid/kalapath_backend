from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from rest_framework import serializers
from sahityo_core.models import Sector,ScheduledCompetition,News,Gallery,Result,Category

# Adjust if your model is in a different app


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    def validate(self, attrs):
        credentials = {
            'email': attrs.get('email'),
            'password': attrs.get('password')
        }

        user = authenticate(**credentials)

        if user is None:
            raise serializers.ValidationError('Invalid login credentials')

        self.user = user
        data = super().validate(attrs)

        data['email'] = self.user.email
        data['role'] = self.user.role

        sector_id = None

        if self.user.role == 'stage':
            try:
                stage = self.user.stage
                data['stage_id'] = str(stage.id)
                data['stage_name'] = stage.name
                sector_id = str(stage.sector.id)
            except:
                data['stage_id'] = None
                data['stage_name'] = None

        elif self.user.role == 'unit':
            try:
                unit = self.user.unit
                data['unit_id'] = str(unit.id)
                data['unit_name'] = unit.name
                sector_id = str(unit.sector.id)
            except:
                data['unit_id'] = None
                data['unit_name'] = None

        elif self.user.role == 'admin':
            try:
                sector = Sector.objects.get(user=self.user)
                sector_id = str(sector.id)
            except:
                pass

        data['sector_id'] = sector_id
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = user.role

        sector_id = None

        if user.role == 'stage':
            try:
                stage = user.stage
                token['stage_id'] = str(stage.id)
                token['stage_name'] = stage.name
                sector_id = str(stage.sector.id)
            except:
                token['stage_id'] = None
                token['stage_name'] = None

        elif user.role == 'unit':
            try:
                unit = user.unit
                token['unit_id'] = str(unit.id)
                token['unit_name'] = unit.name
                sector_id = str(unit.sector.id)
            except:
                token['unit_id'] = None
                token['unit_name'] = None

        elif user.role == 'admin':
            try:
                sector = Sector.objects.get(user=user)
                sector_id = str(sector.id)
            except:
                pass

        token['sector_id'] = sector_id
        return token





class ScheduledCompetitionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledCompetition
        fields = [
            'id',
            'competition',
            'stage',
            'reporting_time',
            'start_time',
            'end_time',
            'date'
        ]
        
        
        
from rest_framework import serializers

class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = ['id', 'competition', 'image']


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['id', 'image', 'created_at']


class GallerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Gallery
        fields = ['id', 'image', 'created_at']


class CategoryCompetitionSerializer(serializers.ModelSerializer):
    competitions = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'competitions']

    def get_competitions(self, obj):
        return [{'id': comp.id, 'name': comp.name} for comp in obj.competition_set.all()]

