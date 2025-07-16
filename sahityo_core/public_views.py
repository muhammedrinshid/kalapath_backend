from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from sahityo_core import Result, News, Gallery, Competition, Category
from sahityo_core.serializers import ResultSerializer, NewsSerializer, GallerySerializer, CategoryCompetitionSerializer

@api_view(['POST'])
def create_result_news_gallery(request):
    """
    Create result, news, or gallery based on the type in request data.
    """
    content_type = request.data.get('type')  # 'result', 'news', or 'gallery'

    if content_type == 'result':
        serializer = ResultSerializer(data=request.data)
    elif content_type == 'news':
        serializer = NewsSerializer(data=request.data)
    elif content_type == 'gallery':
        serializer = GallerySerializer(data=request.data)
    else:
        return Response({'error': 'Invalid type specified.'}, status=status.HTTP_400_BAD_REQUEST)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
def update_result(request, competition_id):
    """
    Update result image for a given competition.
    """
    try:
        result = Result.objects.get(competition__id=competition_id)
    except Result.DoesNotExist:
        return Response({'error': 'Result not found for this competition.'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = ResultSerializer(result, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def category_with_competitions(request):
    """
    Get all categories with competitions.
    """
    categories = Category.objects.all()
    serializer = CategoryCompetitionSerializer(categories, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def top_and_all_news_gallery(request):
    """
    Get top 5 and all news and gallery items.
    """
    top_news = News.objects.order_by('-created_at')[:5]
    top_gallery = Gallery.objects.order_by('-created_at')[:5]

    all_news = News.objects.all()
    all_gallery = Gallery.objects.all()

    return Response({
        'top_news': NewsSerializer(top_news, many=True).data,
        'top_gallery': GallerySerializer(top_gallery, many=True).data,
        'all_news': NewsSerializer(all_news, many=True).data,
        'all_gallery': GallerySerializer(all_gallery, many=True).data,
    })


@api_view(['GET'])
def get_result_by_competition(request, competition_id):
    """
    Get result by competition ID.
    """
    try:
        result = Result.objects.get(competition__id=competition_id)
    except Result.DoesNotExist:
        return Response({'error': 'No result found for this competition.'}, status=status.HTTP_404_NOT_FOUND)
    
    return Response(ResultSerializer(result).data)
