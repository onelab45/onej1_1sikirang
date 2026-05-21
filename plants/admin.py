from django.contrib import admin
from .models import Plant, PlantLog, UserProfile

# Register your models here.

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    UserProfile(사용자 프로필) 모델을 관리하기 위한 Django Admin 설정 클래스입니다.
    """
    list_display = ('nickname', 'created_at', 'last_login_at')
    search_fields = ('nickname',)
    readonly_fields = ('created_at', 'last_login_at')
    # PIN 해시값은 어드민 페이지에 표시되거나 편집되지 않도록 제외 처리
    exclude = ('pin_hash',)


@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    """
    Plant(화분) 모델을 관리하기 위한 Django Admin 설정 클래스입니다.
    """
    list_display = (
        'name', 
        'user',  # 소유 사용자 필드 추가
        'current_weight', 
        'get_watering_date', 
        'get_days_until_watering', 
        'tip', 
        'last_measured_at'
    )
    
    list_filter = ('user', 'last_measured_at')
    search_fields = ('name', 'tip', 'user__nickname')

    @admin.display(description="물주는 예정일")
    def get_watering_date(self, obj):
        return obj.watering_date

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
    """
    list_display = (
        'plant', 
        'event_type', 
        'created_at', 
        'weight_after', 
        'get_detail_summary'
    )
    
    list_filter = ('plant__user', 'event_type', 'created_at')
    search_fields = ('plant__name', 'detail')

    @admin.display(description="상세 내용 요약")
    def get_detail_summary(self, obj):
        if obj.detail and len(obj.detail) > 40:
            return obj.detail[:40] + "..."
        return obj.detail or ""
