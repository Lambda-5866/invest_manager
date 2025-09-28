# investments/views.py
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Asset
from .serializers import AssetSerializer

# 대시보드 페이지
def dashboard_view(request):
    return render(request, "dashboard.html")

# 자산 리스트
@api_view(["GET"])
@permission_classes([AllowAny])
def asset_list(request):
    assets = Asset.objects.all()
    serializer = AssetSerializer(assets, many=True)
    return Response(serializer.data)

# 자산 추가
@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def add_asset(request):
    serializer = AssetSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 자산 삭제
@csrf_exempt
@api_view(["DELETE"])
@permission_classes([AllowAny])
def delete_asset(request, pk):
    try:
        asset = Asset.objects.get(pk=pk)
        asset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Asset.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
