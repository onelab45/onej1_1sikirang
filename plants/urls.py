from django.urls import path
from . import views

# 앱 네임스페이스 정의
app_name = 'plants'

urlpatterns = [
    # 루트 경로: 세션 여부에 따라 홈 또는 로그인 페이지로 분기 리다이렉트
    path('', views.root_view, name='root'),
    
    # 인증 관련 URL
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    
    # 홈 화면 (로그인 완료된 사용자용 화분 목록)
    path('home/', views.home, name='home'),
    
    # 화분 신규 등록 화면 및 처리
    path('plants/new/', views.plant_create, name='plant_create'),
    
    # 화분 상세 정보 조회
    path('plants/<int:pk>/', views.plant_detail, name='plant_detail'),
    
    # 화분 수정 처리 (POST 방식)
    path('plants/<int:pk>/edit/', views.plant_edit, name='plant_edit'),
    
    # "물 줬어요" 처리 API (POST 방식)
    path('plants/<int:pk>/water/', views.plant_water, name='plant_water'),
    
    # 화분 삭제 처리 (POST 방식)
    path('plants/<int:pk>/delete/', views.plant_delete, name='plant_delete'),
    
    # 월간 물주기 캘린더 화면
    path('calendar/', views.calendar_view, name='calendar'),
]
