from django.urls import path
from sahityo_core.public_views import (
    create_result_news_gallery,
    update_result,
    category_with_competitions,
    top_and_all_news_gallery,
    get_result_by_competition,
)

urlpatterns = [
    path('add-news/', create_result_news_gallery, name='create_result_news_gallery'),
    path('update-result/<uuid:pk>/', update_result, name='update_result'),
    path('categories/', category_with_competitions, name='category_with_competitions'),
    path('news-gallery/', top_and_all_news_gallery, name='top_and_all_news_gallery'),
    path('result/<uuid:competition_id>/', get_result_by_competition, name='get_result_by_competition'),
]
