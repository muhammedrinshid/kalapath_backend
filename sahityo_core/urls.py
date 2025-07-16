from django.urls import path, include
from sahityo_core.views import create_stage, create_unit, get_units,get_stages,edit_stage, edit_unit, \
    get_categories,get_competitions_by_category,get_unscheduled_competitions,create_scheduled_competition, \
    scheduled_competitions_by_stage_date,update_scheduled_competition_status,scheduled_competition_detail,\
        update_participant_presence,get_stages_with_competition_details,update_scheduled_competition_times,\
            reset_sector_schedules_and_participants,get_stage_competitions_for_unit,delete_scheduled_competition,\
                get_admin_dashboard_data
        
        



urlpatterns = [
    path('create-stage/', create_stage, name='create_stage'),
    path('create-unit/', create_unit, name='create_unit'),
    # get units of sector
    path('get-units/', get_units, name='get_units'),
    # get stages of sector  
    path('get-stages/', get_stages, name='get_stages'),
    # Include other URLs as needed
    path('edit-stage/<uuid:stage_id>/', edit_stage, name='edit_stage'),
    path('edit-unit/<uuid:unit_id>/', edit_unit, name='edit_unit'),
    
    # get categories
    path('get-categories/', get_categories, name='get_categories'),
    # get competitions by category
    path('get-competitions-by-category/', get_competitions_by_category, name='get_competitions_by_category'),
    # get unscheduled competitions
    path('get-unscheduled-competitions/<uuid:category_id>/', get_unscheduled_competitions, name='get_unscheduled_competitions'),

    # create scheduled competition
    path('create-scheduled-competition/<uuid:stage_id>', create_scheduled_competition, name='create_scheduled_competition'),
    
    # get scheduled competitions by stage and date
    path('scheduled-competitions-by-stage-date/<uuid:stage_id>/', scheduled_competitions_by_stage_date, name='scheduled_competitions_by_stage_date'),
    
    # update scheduled competition status
    path('update-scheduled-competition-status/<uuid:scheduled_competition_id>/', update_scheduled_competition_status, name='update_scheduled_competition_status'),
    
    # get scheduled competition details
    path('scheduled-competition-detail/<uuid:scheduled_competition_id>/', scheduled_competition_detail, name='scheduled_competition_detail'),
    
    # update participant presence
    path('update-participant-presence/<uuid:participant_present_id>/', update_participant_presence, name='update_participant_presence'),
    
    # get stages with competition details
    path('get-stages-with-competition-details/<uuid:unit_id>/<str:date>/', get_stages_with_competition_details, name='get_stages_with_competition_details'),
    
    # update scheduled competition times
    path('update-scheduled-competition-times/<uuid:scheduled_competition_id>/', update_scheduled_competition_times, name='update_scheduled_competition_times'),
    
    # reset sector schedules and participants
    path('reset-sector-schedules-and-participants/', reset_sector_schedules_and_participants, name='reset_sector_schedules_and_participants'),

    # 
    path('get-stage-competitions-for-unit/<uuid:stage_id>/<uuid:unit_id>/', get_stage_competitions_for_unit, name='get_stage_competitions_for_unit'),
    
    # delete scheduled competition
    path('delete-scheduled-competition/<uuid:scheduled_competition_id>/', delete_scheduled_competition, name='delete_scheduled_competition'),
    
    # get admin dashboard data
    path('get-admin-dashboard-data/', get_admin_dashboard_data, name='get_admin_dashboard_data'),
]