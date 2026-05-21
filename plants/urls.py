from django.urls import path
from . import views

# 앱 네임스페이스 정의
app_name = 'plants'

urlpatterns = [
    # 홈 화면 (물주기 임박 알림 및 화분 목록)
    path('', views.home, name='home'),
    
    # 화분 신규 등록 화면 및 처리
    path('plants/add/', views.plant_create, name='plant_create'),
    
    # 화분 상세 정보 조회 및 수정 처리
    path('plants/<int:pk>/', views.plant_detail, name='plant_detail'),
    
    # "물 줬어요" 처리 API (POST 방식)
    path('plants/<int:pk>/water/', views.plant_water, name='plant_water'),
    
    # 화분 삭제 처리 (POST 방식)
    path('plants/<int:pk>/delete/', views.plant_delete, name='plant_delete'),
    
    # 월간 물주기 캘린더 화면
    path('calendar/', views.calendar_view, name='calendar'),
]
