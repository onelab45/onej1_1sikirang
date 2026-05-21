from django.contrib import admin
from .models import Plant, PlantLog

# Register your models here.

@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    """
    Plant(화분) 모델을 관리하기 위한 Django Admin 설정 클래스입니다.
    목록 화면에서 화분 이름, 현재 무게, 물주는 예정일, 남은 일수 등을 한눈에 볼 수 있도록 구성합니다.
    """
    # 2단계 보완: season 삭제, tip 추가
    list_display = (
        'name', 
        'current_weight', 
        'get_watering_date', 
        'get_days_until_watering', 
        'tip', 
        'last_measured_at'
    )
    
    # 우측 필터 옵션 (season 삭제)
    list_filter = ('last_measured_at',)
    
    # 검색 창 설정
    search_fields = ('name', 'tip')

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


@admin.register(PlantLog)
class PlantLogAdmin(admin.ModelAdmin):
    """
    PlantLog(화분 이력 로그) 모델을 관리하기 위한 Django Admin 설정 클래스입니다.
    등록, 물주기, 설정 변경 등 화분의 모든 이벤트를 요약 표시합니다.
    """
    list_display = (
        'plant', 
        'event_type', 
        'created_at', 
        'weight_after', 
        'get_detail_summary'
    )
    
    list_filter = ('plant', 'event_type', 'created_at')
    search_fields = ('plant__name', 'detail')

    # 상세 내용 요약 출력 메서드
    @admin.display(description="상세 내용 요약")
    def get_detail_summary(self, obj):
        if obj.detail and len(obj.detail) > 40:
            return obj.detail[:40] + "..."
        return obj.detail or ""
