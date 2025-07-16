from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from .models import Sector, Unit,User,Stage,Category,Competition,ScheduledCompetition,ParticipantPresent
from sahityo_core.serializers import ScheduledCompetitionCreateSerializer
from django.db import transaction
import uuid
from datetime import datetime
from django.utils import timezone
import pytz
from django.db.models import Q
import traceback
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken
from django.core.exceptions import ObjectDoesNotExist




def parse_utc_datetime(dt_str):
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class DebugTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except InvalidToken as e:
            print("InvalidToken Exception:", str(e))
            print(traceback.format_exc())
            return Response({'error': 'Invalid or expired refresh token'}, status=401)
        except Exception as e:
            print("Unexpected Error:", str(e))
            print(traceback.format_exc())
            return Response({'error': 'Internal server error'}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def create_stage(request):
    sector_id = request.query_params.get('sector_id')
    print(f"Received sector_id: {sector_id}")
    name = request.data.get('name')
    email = request.data.get('email')
    password = request.data.get('password')

    if not all([name, email, password, sector_id]):
        print("Missing fields in request data")
        print(f"Received data: {request.data}, sector_id: {sector_id}")
        return Response({'error': 'Missing fields'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        Sector.objects.get(id=sector_id)
    except Sector.DoesNotExist:
        
        return Response({'error': 'Sector not found'}, status=status.HTTP_404_NOT_FOUND)

    user = User.objects.create(
        id=uuid.uuid4(),
        email=email,
        password=make_password(password),
        role='stage'
    )
    Stage.objects.create(
        id=uuid.uuid4(),
        name=name,
        sector_id=sector_id,
        user=user
    )
    return Response({'message': 'Stage created successfully', 'user_id': str(user.id)}, status=status.HTTP_201_CREATED)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def create_unit(request):
    sector_id = request.query_params.get('sector_id')
    name = request.data.get('name')
    email = request.data.get('email')
    password = request.data.get('password')

    if not all([name, email, password, sector_id]):
        return Response({'error': 'Missing fields'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        sector = Sector.objects.get(id=sector_id)
    except Sector.DoesNotExist:
        return Response({'error': 'Sector not found'}, status=status.HTTP_404_NOT_FOUND)

    user = User.objects.create(
        id=uuid.uuid4(),
        email=email,
        password=make_password(password),
        role='unit'
    )

    Unit.objects.create(
        id=uuid.uuid4(),
        name=name,
        sector=sector,
        user=user
    )

    return Response({'message': 'Unit created successfully', 'user_id': str(user.id)}, status=status.HTTP_201_CREATED)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def edit_stage(request, stage_id):
    if request.user.role != 'admin':
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    name = request.data.get('name')
    email = request.data.get('email')
    password = request.data.get('password', '')

    try:
        stage = Stage.objects.get(id=stage_id)
    except Stage.DoesNotExist:
        return Response({'error': 'Stage not found'}, status=status.HTTP_404_NOT_FOUND)
    # check email already exists
    if email and User.objects.filter(email=email).exclude(id=stage.user.id).exists():
        return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)  
    user = stage.user

    user.email = email or user.email
    if password:
        user.password = make_password(password)
    user.save()

    stage.name = name or stage.name
    stage.save()

    return Response({'message': 'Stage updated successfully'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_admin_dashboard_data(request):
    sector_id = request.query_params.get('sector_id')
    if not sector_id:
        return Response({'error': 'sector_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        sector = Sector.objects.get(id=sector_id)

        # Total competitions remaining (not scheduled in this sector)
        all_competitions = Competition.objects.all()
        scheduled_ids = ScheduledCompetition.objects.filter(sector_id=sector_id).values_list('competition_id', flat=True)
        remaining_competitions = all_competitions.exclude(id__in=scheduled_ids)
        total_remaining = remaining_competitions.count()

        # Competitions by category (remaining)
        categories = Category.objects.all()
        competitions_by_category = []
        for category in categories:
            cat_comps = Competition.objects.filter(category=category)
            scheduled_cat_ids = ScheduledCompetition.objects.filter(
                sector_id=sector_id,
                competition__category=category
            ).values_list('competition_id', flat=True)
            remaining_cat_comps = cat_comps.exclude(id__in=scheduled_cat_ids)
            competitions_by_category.append({
                'category_id': str(category.id),
                'category_name': category.name,
                'remaining_competitions': remaining_cat_comps.count()
            })

        # Total stages in this sector
        total_stages = Stage.objects.filter(sector=sector).count()

        # Total units in this sector
        total_units = Unit.objects.filter(sector=sector).count()

        dashboard_data = {
            'total_remaining_competitions': total_remaining,
            'competitions_by_category': competitions_by_category,
            'total_stages': total_stages,
            'total_units': total_units
        }
        return Response(dashboard_data, status=status.HTTP_200_OK)
    except Sector.DoesNotExist:
        return Response({'error': 'Sector not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def edit_unit(request, unit_id):
    if request.user.role != 'admin':
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    name = request.data.get('name')
    email = request.data.get('email')
    password = request.data.get('password', '')

    try:
        unit = Unit.objects.get(id=unit_id)
    except Unit.DoesNotExist:
        return Response({'error': 'Unit not found'}, status=status.HTTP_404_NOT_FOUND)

    # check email already exists
    if email and User.objects.filter(email=email).exclude(id=unit.user.id).exists():
        return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)
    user = unit.user

    user.email = email or user.email
    if password:
        user.password = make_password(password)
    user.save()

    unit.name = name or unit.name
    unit.save()

    return Response({'message': 'Unit updated successfully'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_units(request):
    sector_id = request.query_params.get('sector_id')
    if not sector_id:
        return Response({'error': 'Sector ID is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        sector = Sector.objects.get(id=sector_id)
    except Sector.DoesNotExist:
        return Response({'error': 'Sector not found'}, status=status.HTTP_404_NOT_FOUND)

    units = sector.units.all()
    unit_list = [{'id': str(unit.id), 'name': unit.name, 'email': unit.user.email} for unit in units]
    return Response({'units': unit_list}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_stages(request):
    sector_id = request.query_params.get('sector_id')
    if not sector_id:
        return Response({'error': 'Sector ID is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        sector = Sector.objects.get(id=sector_id)
    except Sector.DoesNotExist:
        return Response({'error': 'Sector not found'}, status=status.HTTP_404_NOT_FOUND)

    stages = sector.stages.all()
    stage_list = [{'id': str(stage.id), 'name': stage.name, 'email': stage.user.email} for stage in stages]

    return Response({'stages': stage_list}, status=status.HTTP_200_OK)





@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_categories(request):
    categories = Category.objects.all()
    data = [{'id': str(category.id), 'name': category.name} for category in categories]
    return Response({'categories': data}, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_competitions_by_category(request):
    category_id = request.GET.get('category_id')
    if not category_id:
        return Response({'error': 'category_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

    competitions = category.competition_set.all()
    data = [{'id': str(comp.id), 'name': comp.name} for comp in competitions]
    return Response({'competitions': data}, status=status.HTTP_200_OK)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unscheduled_competitions(request,category_id):
    sector_id = request.query_params.get('sector_id')

    if not category_id:
        return Response({"error": "category_id is required as a query parameter"}, status=status.HTTP_400_BAD_REQUEST)

    # All competitions in this category
    competitions = Competition.objects.filter(category_id=category_id)

    # Already scheduled competitions for this sector
    scheduled_ids = ScheduledCompetition.objects.filter(sector_id=sector_id).values_list('competition_id', flat=True)
    print(f"Scheduled competition IDs: {scheduled_ids}")

    # Filter unscheduled competitions
    unscheduled = competitions.exclude(id__in=scheduled_ids)
    print(f"Unscheduled competitions: {unscheduled}")

    # Manually serialize the required fields
    data = [
        {
            "id": comp.id,
            "name": comp.name,
            "category": {
                "id": comp.category.id,
                "name": comp.category.name
            }
        }
        for comp in unscheduled
    ]

    return Response({"unscheduled_competitions": data}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_scheduled_competition(request, stage_id):
    data = request.data
    sector_id = request.query_params.get('sector_id')

    if not stage_id or not sector_id:
        return Response({'error': 'Stage ID and Sector ID are required'}, status=status.HTTP_400_BAD_REQUEST)

    required_fields = ['competition_id', 'date', 'reporting_time', 'start_time', 'end_time']
    for field in required_fields:
        if field not in data:
            return Response({'error': f'{field} is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        sector = Sector.objects.get(id=sector_id)
        stage = Stage.objects.get(id=stage_id)
        competition = Competition.objects.get(id=data['competition_id'])

        # Always assuming frontend sent valid UTC strings
        date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        reporting_time = datetime.fromisoformat(data['reporting_time'].replace("Z", "+00:00"))
        start_time = datetime.fromisoformat(data['start_time'].replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(data['end_time'].replace("Z", "+00:00"))

        overlapping = ScheduledCompetition.objects.filter(
            stage=stage,
            date=date
        ).filter(
            Q(start_time__lt=end_time) & Q(end_time__gt=start_time)
        )

        if overlapping.exists():
            return Response({'error': 'Conflict: another competition exists in this time range.'}, status=status.HTTP_400_BAD_REQUEST)

        scheduled = ScheduledCompetition.objects.create(
            id=uuid.uuid4(),
            competition=competition,
            sector=sector,
            stage=stage,
            date=date,
            reporting_time=reporting_time,
            start_time=start_time,
            end_time=end_time,
        )

        return Response({'message': 'Scheduled competition created', 'id': str(scheduled.id)}, status=status.HTTP_201_CREATED)

    except (Sector.DoesNotExist, Stage.DoesNotExist, Competition.DoesNotExist) as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        print("Error creating scheduled competition:", str(e))
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def delete_scheduled_competition(request, scheduled_competition_id):
    try:
        scheduled = ScheduledCompetition.objects.get(id=scheduled_competition_id)
        # Delete related participant presence records
        ParticipantPresent.objects.filter(scheduled_competition=scheduled).delete()
        scheduled.delete()
        return Response({'message': 'Scheduled competition deleted successfully.'}, status=status.HTTP_200_OK)
    except ScheduledCompetition.DoesNotExist:
        return Response({'error': 'Scheduled competition not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        print("Error deleting scheduled competition:", str(e))
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scheduled_competitions_by_stage_date(request, stage_id):
    date_str = request.query_params.get('date')
    
    if not date_str:
        return Response({'error': 'Date is required (YYYY-MM-DD)'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

    competitions = ScheduledCompetition.objects.filter(stage_id=stage_id, date=date)

    data = []
    
    for sc in competitions:
        data.append({
            'id': str(sc.id),
            'competition': {
                'id': str(sc.competition.id),
                'name': sc.competition.name,
                'category': {
                    'id': str(sc.competition.category.id),
                    'name': sc.competition.category.name,
                }
            },
            'sector': {
                'id': str(sc.sector.id),
                'name': sc.sector.name,
            },
            'reporting_time': sc.reporting_time,
            'start_time': sc.start_time,
            'end_time': sc.end_time,
            'status': sc.status,
        })

    return Response({'scheduled_competitions': data}, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def update_scheduled_competition_status(request, scheduled_competition_id):
    new_status = request.data.get('status')

    if new_status not in dict(ScheduledCompetition.STATUS_CHOICES):
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        competition = ScheduledCompetition.objects.get(id=scheduled_competition_id)

        # Manual validation for unique 'ongoing' and 'reporting' statuses per stage per date
        if new_status in ['ongoing', 'reporting']:
            exists = ScheduledCompetition.objects.filter(
                stage=competition.stage,
                date=competition.date,
                status=new_status
            ).exclude(id=competition.id).exists()

            if exists:
                return Response(
                    {'error': f'Another competition with status "{new_status}" already exists for this stage and date.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if new_status == "not_started":
                presents_to_delete = ParticipantPresent.objects.filter(
                    scheduled_competition=competitionx
                )
                presents_to_delete.delete()
        # Update status
        competition.status = new_status
        competition.save(update_fields=['status'])
        return Response({'message': 'Status updated successfully'}, status=status.HTTP_200_OK)

    except ScheduledCompetition.DoesNotExist:
        return Response({'error': 'Scheduled competition not found'}, status=status.HTTP_404_NOT_FOUND)

    
    
    
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scheduled_competition_detail(request, scheduled_competition_id):
    """
    Retrieve detailed information for a ScheduledCompetition by ID.
    If participants do not exist, create them for all units in the sector.
    """
    try:
        competition = ScheduledCompetition.objects.get(id=scheduled_competition_id)
        
        # If no participants exist, create them for all units in the sector
        if not competition.participants.exists():
            units = Unit.objects.filter(sector=competition.sector)
            participant_records = []
            for unit in units:
                participant_records.append(
                    ParticipantPresent(
                        scheduled_competition=competition,
                        unit=unit,
                        participant_1_present=False,
                        participant_2_present=False
                    )
                )
            ParticipantPresent.objects.bulk_create(participant_records)
        
        # Construct the response data manually
        response_data = {
            'id': str(competition.id),
            'competition': {
                'id': str(competition.competition.id),
                'name': competition.competition.name,
                'category': {
                    'id': str(competition.competition.category.id),
                    'name': competition.competition.category.name
                }
            },
            'sector': {
                'id': str(competition.sector.id),
                'name': competition.sector.name
            },
            'reporting_time': competition.reporting_time.isoformat(),
            'date': competition.date.isoformat() if competition.date else None,
            'start_time': competition.start_time.isoformat(),
            'end_time': competition.end_time.isoformat(),
            'status': competition.status,
            'participants': [
                {
                    'id': str(participant.id),
                    'unit': {
                        'id': str(participant.unit.id),
                        'name': participant.unit.name
                    },
                    'participant_1_present': participant.participant_1_present,
                    'participant_2_present': participant.participant_2_present,
                    'created_at': participant.created_at.isoformat(),
                    'updated_at': participant.updated_at.isoformat()
                }
                for participant in competition.participants.all()
            ]
        }
        
        return Response({'scheduled_competition_details': response_data}, status=status.HTTP_200_OK)
    except ScheduledCompetition.DoesNotExist:
        return Response({'error': 'Competition not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_participant_presence(request, participant_present_id):
    """
    Update participant presence for a ParticipantPresent entry by ID.
    """
    try:
        participant = ParticipantPresent.objects.get(id=participant_present_id)
        
        # Get data from request body
        data = request.data
        participant_1_present = data.get('participant_1_present', participant.participant_1_present)
        participant_2_present = data.get('participant_2_present', participant.participant_2_present)
        
        # Update only provided fields
        if 'participant_1_present' in data:
            participant.participant_1_present = participant_1_present
        if 'participant_2_present' in data:
            participant.participant_2_present = participant_2_present
        
        # Save the updated participant
        participant.save()
        
        # Construct the response data
        response_data = {
            'id': str(participant.id),
            'unit': {
                'id': str(participant.unit.id),
                'name': participant.unit.name
            },
            'participant_1_present': participant.participant_1_present,
            'participant_2_present': participant.participant_2_present,
            'created_at': participant.created_at.isoformat(),
            'updated_at': participant.updated_at.isoformat()
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    except ParticipantPresent.DoesNotExist:
        return Response({'error': 'Participant not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_stages_with_competition_details(request, unit_id, date):
    try:
        sector_id = request.query_params.get('sector_id')
        if not sector_id:
            return Response({"error": "sector_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not unit_id:
            return Response({"error": "unit_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not date:
            return Response({"error": "date is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        stages = Stage.objects.filter(sector_id=sector_id)
        if not stages.exists():
            return Response({"error": "No stages found for the given sector"}, status=status.HTTP_404_NOT_FOUND)

        response_data = []

        for stage in stages:
            stage_data = {
                "id": str(stage.id),
                "name": stage.name,
                "ongoing_competition": None,
                "reporting_competition": None,
                "reporting_time": None,
                "date": None,
                "start_time": None,
                "end_time": None
            }

            scheduled_competitions = ScheduledCompetition.objects.filter(
                stage=stage,
                date=date
            ).select_related('competition__category', 'sector')

            # Ongoing competition
            ongoing = scheduled_competitions.filter(status='ongoing').first()
            if ongoing:
                presence = ParticipantPresent.objects.filter(
                    scheduled_competition=ongoing,
                    unit_id=unit_id
                ).first()

                stage_data["ongoing_competition"] = {
                    "id": str(ongoing.id),
                    "name": ongoing.competition.name,
                    "category": {
                        "id": str(ongoing.competition.category.id),
                        "name": ongoing.competition.category.name
                    },
                    "status": ongoing.status,
                    "start_time": ongoing.start_time.isoformat(),
                    "end_time": ongoing.end_time.isoformat(),
                    "is_your_first_candidate_present": presence.participant_1_present if presence else False,
                    "is_your_second_candidate_present": presence.participant_2_present if presence else False
                }

                stage_data["reporting_time"] = ongoing.reporting_time.isoformat()
                stage_data["date"] = ongoing.date.isoformat()
                stage_data["start_time"] = ongoing.start_time.isoformat()
                stage_data["end_time"] = ongoing.end_time.isoformat()

            # Reporting competition
            reporting = scheduled_competitions.filter(status='reporting').first()
            if reporting:
                presence = ParticipantPresent.objects.filter(
                    scheduled_competition=reporting,
                    unit_id=unit_id
                ).first()

                stage_data["reporting_competition"] = {
                    "id": str(reporting.id),
                    "name": reporting.competition.name,
                    "category": {
                        "id": str(reporting.competition.category.id),
                        "name": reporting.competition.category.name
                    },
                    "status": reporting.status,
                    "reporting_time": reporting.reporting_time.isoformat(),
                    "start_time": reporting.start_time.isoformat(),
                    "end_time": reporting.end_time.isoformat(),
                    "is_your_first_candidate_present": presence.participant_1_present if presence else False,
                    "is_your_second_candidate_present": presence.participant_2_present if presence else False
                }

                if not stage_data["reporting_time"]:
                    stage_data["reporting_time"] = reporting.reporting_time.isoformat()
                    stage_data["date"] = reporting.date.isoformat()
                    stage_data["start_time"] = reporting.start_time.isoformat()
                    stage_data["end_time"] = reporting.end_time.isoformat()

            response_data.append(stage_data)

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        print("Error in get_stages_with_competition_details:", str(e))
        print(traceback.format_exc())
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_scheduled_competition_times(request, scheduled_competition_id):
    """
    Update reporting_time, start_time, and end_time for a ScheduledCompetition.
    """
    try:
        competition = ScheduledCompetition.objects.get(id=scheduled_competition_id)
        data = request.data

        reporting_time = data.get('reporting_time')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        if not all([reporting_time, start_time, end_time]):
            return Response({'error': 'reporting_time, start_time, and end_time are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Parse UTC ISO datetime strings
        competition.reporting_time = datetime.fromisoformat(reporting_time.replace("Z", "+00:00"))
        competition.start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        competition.end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

        # Save updated times
        competition.save()

        return Response({'message': 'Scheduled competition times updated successfully.'}, status=status.HTTP_200_OK)

    except ScheduledCompetition.DoesNotExist:
        return Response({'error': 'Scheduled competition not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(traceback.format_exc())
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_sector_schedules_and_participants(request):
    """
    Admin-only view to delete ScheduledCompetition and ParticipantPresent records for a specific sector.
    Sector ID should be provided as a query parameter (?sector_id=...).
    """
    if request.user.role != 'admin':
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    sector_id = request.query_params.get('sector_id')
    if not sector_id:
        return Response({'error': 'sector_id is required as a query parameter'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        with transaction.atomic():
            # Get scheduled competitions for the sector
            scheduled_ids = ScheduledCompetition.objects.filter(sector_id=sector_id).values_list('id', flat=True)
            # Delete related ParticipantPresent records
            ParticipantPresent.objects.filter(scheduled_competition_id__in=scheduled_ids).delete()
            # Delete ScheduledCompetition records
            ScheduledCompetition.objects.filter(id__in=scheduled_ids).delete()
        return Response({'message': 'Schedules and participant presence data for the sector have been reset.'}, status=status.HTTP_200_OK)
    except Exception as e:
        print(traceback.format_exc())
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
    
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_stage_competitions_for_unit(request, stage_id,unit_id):
    
    sector_id = request.query_params.get('sector_id')


    # Validate input
    if not stage_id or not unit_id:
        return Response(
            {'error': 'stage_id and unit_id are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Fetch scheduled competitions for the given stage and sector
        
        stage = Stage.objects.get(id=stage_id)
        scheduled_competitions = ScheduledCompetition.objects.filter(
            stage_id=stage_id,
            sector_id=sector_id
        ).select_related('competition', 'competition__category', 'stage', 'sector')

        # Prepare response data
        response_data = {
            'stage_name': '',
            'stage_id': stage_id,
            'scheduled_competitions': []
        }

        # Get stage name if competitions exist
        if scheduled_competitions.exists():
            response_data['stage_name'] = stage.name

        # Process each scheduled competition
        for comp in scheduled_competitions:
            # Fetch participant presence status for the given unit
            try:
                participant_status = ParticipantPresent.objects.get(
                    scheduled_competition_id=comp.id,
                    unit_id=unit_id
                )
                participant1_present = participant_status.participant_1_present
                participant2_present = participant_status.participant_2_present
            except ObjectDoesNotExist:
                participant1_present = False
                participant2_present = False

            comp_data = {
                'id': str(comp.id),
                'name': comp.competition.name,
                'category': {
                    'id': str(comp.competition.category.id),
                    'name': comp.competition.category.name
                },
                'participant1_present_status': participant1_present,
                'participant2_present_status': participant2_present,
                'reporting_time': comp.reporting_time.isoformat() if comp.reporting_time else None,
                'date': comp.date.isoformat() if comp.date else None,
                'start_time': comp.start_time.isoformat() if comp.start_time else None,
                'end_time': comp.end_time.isoformat() if comp.end_time else None,
                'status': comp.status
            }
            response_data['scheduled_competitions'].append(comp_data)

        # Sort competitions by status priority and time
        status_priority = {'reporting': 1, 'ongoing': 2, 'not_started': 3, 'finished': 4}
        response_data['scheduled_competitions'].sort(
            key=lambda x: (
                status_priority.get(x['status'], 5),
                x['reporting_time'] or datetime.datetime.max.isoformat()
            )
        )

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Failed to fetch stage details: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )