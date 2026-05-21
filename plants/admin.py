from django.contrib import admin
from .models import Plant, WaterLog

# Register your models here.

@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    """
    Plant(화분) 모델을 관리하기 위한 Django Admin 설정 클래스입니다.
    목록 화면에서 화분 이름, 현재 무게, 물주는 예정일, 남은 일수 등을 한눈에 볼 수 있도록 구성합니다.
    """
    # 목록 페이지에 표시할 필드들
    list_display = (
        'name', 
        'current_weight', 
        'get_watering_date', 
        'get_days_until_watering', 
        'season', 
        'last_measured_at'
    )
    
    # 우측 필터 옵션
    list_filter = ('season', 'last_measured_at')
    
    # 검색 창 설정
    search_fields = ('name',)

    # 어드민 목록 뷰에서 모델 프로퍼티(watering_date)를 한글 필드명으로 노출하기 위한 데코레이터 메서드
    @admin.display(description="물주는 예정일")
    def get_watering_date(self, obj):
        return obj.watering_date

    # 어드민 목록 뷰에서 모델 프로퍼티(days_until_watering)를 한글 필드명 및 커스텀 텍스트로 노출
    @admin.display(description="물주기 D-Day")
    def get_days_until_watering(self, obj):
        days = obj.days_until_watering
        if days < 0:
            return f"물주기 지남 ({abs(days)}일 초과)"
        elif days == 0:
            return "★ 오늘 물주기!"
        else:
            return f"D-{days} (일 남음)"


@admin.register(WaterLog)
class WaterLogAdmin(admin.ModelAdmin):
    """
    WaterLog(물주기 이력) 모델을 관리하기 위한 Django Admin 설정 클래스입니다.
    어떤 화분에 언제 물을 주었는지, 물 준 후 무게와 메모를 기록한 목록을 표시합니다.
    """
    # 목록 페이지에 표시할 필드들
    list_display = (
        'plant', 
        'watered_at', 
        'weight_after', 
        'memo'
    )
    
    # 우측 필터 옵션
    list_filter = ('plant', 'watered_at')
    
    # 검색 창 설정
    search_fields = ('plant__name', 'memo')
