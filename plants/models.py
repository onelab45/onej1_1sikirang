from django.db import models
from django.utils import timezone
import datetime

# Create your models here.

class Plant(models.Model):
    """
    화분 정보를 저장하는 모델입니다.
    각 화분의 현재 무게, 하루 물 감소량, 물을 주어야 하는 한계 무게, 계절 등을 관리합니다.
    """
    
    # 계절 선택 옵션 정의
    SEASON_CHOICES = [
        ('spring', '봄'),
        ('summer', '여름'),
        ('fall', '가을'),
        ('winter', '겨울'),
    ]
    
    name = models.CharField(
        max_length=50, 
        verbose_name="화분 이름"
    )
    current_weight = models.FloatField(
        verbose_name="현재 무게(g)"
    )
    daily_decrease = models.FloatField(
        verbose_name="1일 감소량(g)"
    )
    water_threshold = models.FloatField(
        verbose_name="물주는 무게(g)"
    )
    season = models.CharField(
        max_length=10, 
        choices=SEASON_CHOICES, 
        verbose_name="현재 계절"
    )
    # auto_now나 auto_now_add를 사용하지 않고 직접 입력 및 갱신합니다. 기본값은 현재 시각입니다.
    last_measured_at = models.DateTimeField(
        default=timezone.now, 
        verbose_name="마지막 측정 시각"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="등록 일시"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="수정 일시"
    )

    class Meta:
        verbose_name = "화분"
        verbose_name_plural = "화분 목록"
        ordering = ['-created_at']

    @property
    def estimated_weight_today(self):
        """
        오늘 예상 무게를 계산하여 반올림한 값을 소수점 첫째 자리까지 반환합니다.
        공식: 현재 무게 - (1일 감소량 * (오늘 - 마지막 측정일 경과일수))
        """
        # 마지막 측정일로부터 오늘까지 경과한 시간 계산 (초 단위)
        now = timezone.now()
        delta = now - self.last_measured_at
        
        # 경과한 시간을 일(day) 단위 실수로 변환
        days_passed = delta.total_seconds() / 86400.0
        
        # 측정 시각이 미래일 경우를 방지하여 경과 일수를 최소 0으로 보장
        if days_passed < 0:
            days_passed = 0.0
            
        # 예상 무게 계산
        weight = self.current_weight - (self.daily_decrease * days_passed)
        
        # 무게는 0g 미만으로 떨어지지 않도록 제한하고 소수점 1자리 반올림
        return round(max(0.0, weight), 1)

    @property
    def days_until_watering(self):
        """
        물주기까지 남은 일수를 정수로 반환합니다. (음수 가능)
        공식: (물주기 예정일 - 오늘) 일수
        """
        # 물주기 예정일(date 객체)과 오늘(date 객체)의 차이를 계산
        today = timezone.localdate()
        w_date = self.watering_date
        
        # 날짜 차이(일수) 반환
        return (w_date - today).days

    @property
    def watering_date(self):
        """
        물줘야 하는 예상 날짜(date 객체)를 계산하여 반환합니다.
        공식: 마지막 측정 시각 + ((현재 무게 - 물주는 무게) / 1일 감소량) 일
        """
        # 1일 감소량이 0 이하일 경우 예외적으로 오늘 날짜를 반환 (나누기 0 방지)
        if self.daily_decrease <= 0:
            return timezone.localdate()
            
        # 마지막 측정 시점부터 물주는 무게에 도달할 때까지 걸리는 일수 계산
        days_to_threshold = (self.current_weight - self.water_threshold) / self.daily_decrease
        
        # 마지막 측정 시각에 위 일수를 더해 물주기 예상 시각(datetime) 도출
        watering_datetime = self.last_measured_at + datetime.timedelta(days=days_to_threshold)
        
        # 장고 표준 시간대에 맞춰 로컬 날짜(date) 객체로 변환하여 반환
        return timezone.localtime(watering_datetime).date()

    @property
    def is_watering_due(self):
        """
        물주기 예정일이 오늘이거나 이미 지났는지 여부를 반환합니다.
        """
        return self.days_until_watering <= 0

    def __str__(self):
        return self.name


class WaterLog(models.Model):
    """
    화분의 물주기 이력을 저장하는 모델입니다.
    어떤 화분에 언제 물을 주었는지, 물을 준 직후 무게와 메모를 기록합니다.
    """
    plant = models.ForeignKey(
        Plant, 
        on_delete=models.CASCADE, 
        related_name='water_logs',
        verbose_name="화분"
    )
    watered_at = models.DateTimeField(
        default=timezone.now, 
        verbose_name="물 준 시각"
    )
    weight_after = models.FloatField(
        verbose_name="물 준 후 무게(g)"
    )
    memo = models.TextField(
        blank=True, 
        verbose_name="메모"
    )

    class Meta:
        verbose_name = "물주기 이력"
        verbose_name_plural = "물주기 이력 목록"
        ordering = ['-watered_at']

    def __str__(self):
        # 로컬 시간대로 물 준 시각 변환하여 출력 형식 구성
        local_watered_at = timezone.localtime(self.watered_at)
        formatted_time = local_watered_at.strftime('%Y-%m-%d %H:%M')
        return f"{self.plant.name} - {formatted_time}"
