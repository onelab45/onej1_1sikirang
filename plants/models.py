from django.db import models
from django.utils import timezone
import datetime

# Create your models here.

class Plant(models.Model):
    """
    화분 정보를 저장하는 모델입니다.
    각 화분의 현재 무게, 하루 물 감소량, 물을 주어야 하는 한계 무게, 관리 팁 등을 관리합니다.
    """
    
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
    # 2단계 보완: 계절(season) 삭제 및 관리 Tip 필드 추가
    tip = models.TextField(
        blank=True, 
        verbose_name="관리 Tip 메모"
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

    def save(self, *args, **kwargs):
        """
        save() 메서드를 오버라이드하여 화분 생성(created) 및 수정(updated)에 대한
        이력 로그(PlantLog)를 자동으로 남깁니다.
        """
        is_new = self.pk is None
        
        if is_new:
            # 신규 등록인 경우: 먼저 부모 save()를 호출하여 기본 키(pk)를 발급받습니다.
            super().save(*args, **kwargs)
            
            # 화분 등록 이력 생성
            detail_msg = f"초기값: {self.current_weight}g / 1일 {self.daily_decrease}g 감소 / 물주기 {self.water_threshold}g"
            if self.tip:
                detail_msg += f"\nTip: {self.tip}"
                
            self.logs.create(
                event_type='created',
                created_at=self.last_measured_at,
                weight_after=self.current_weight,
                detail=detail_msg
            )
        else:
            # 정보 수정인 경우: DB에 저장된 수정 전 데이터를 조회하여 변경점을 대조합니다.
            original = Plant.objects.get(pk=self.pk)
            changes = []
            
            # 필드별 변경 대조
            if original.name != self.name:
                changes.append(f"이름: {original.name} → {self.name}")
                
            # 무게 변경 검증 (물주기 뷰에서 갱신하는 경우 제외)
            if original.current_weight != self.current_weight:
                if not getattr(self, '_is_watering', False):
                    changes.append(f"무게: {original.current_weight}g → {self.current_weight}g")
                    
            if original.daily_decrease != self.daily_decrease:
                changes.append(f"1일 감소량: {original.daily_decrease}g → {self.daily_decrease}g")
                
            if original.water_threshold != self.water_threshold:
                changes.append(f"물주는 무게: {original.water_threshold}g → {self.water_threshold}g")
                
            if original.tip != self.tip:
                old_tip = f'"{original.tip}"' if original.tip else '(없음)'
                new_tip = f'"{self.tip}"' if self.tip else '(없음)'
                changes.append(f"Tip 변경: {old_tip} → {new_tip}")
                
            # 부모 save() 호출하여 실제 데이터베이스 저장 완료
            super().save(*args, **kwargs)
            
            # 변경 이력이 존재하는 경우에만 설정 변경 로그를 자동으로 생성
            if changes:
                detail_msg = "\n".join(changes)
                self.logs.create(
                    event_type='updated',
                    detail=detail_msg
                )

    def __str__(self):
        return self.name


class PlantLog(models.Model):
    """
    화분의 이력을 저장하는 통합 로그 모델입니다.
    화분 등록, 물주기, 설정 변경 등의 이벤트를 구분하여 기록합니다.
    """
    EVENT_CHOICES = [
        ('created', '화분 등록'),
        ('watered', '물 줬어요'),
        ('updated', '설정 변경'),
    ]
    
    plant = models.ForeignKey(
        Plant, 
        on_delete=models.CASCADE, 
        related_name='logs',
        verbose_name="화분"
    )
    event_type = models.CharField(
        max_length=10,
        choices=EVENT_CHOICES,
        verbose_name="이벤트 종류"
    )
    created_at = models.DateTimeField(
        default=timezone.now, 
        verbose_name="기록 시각"
    )
    weight_after = models.FloatField(
        null=True,
        blank=True,
        verbose_name="기록 시점 무게(g)"
    )
    detail = models.TextField(
        blank=True, 
        verbose_name="상세 내용"
    )

    class Meta:
        verbose_name = "화분 이력 로그"
        verbose_name_plural = "화분 이력 로그 목록"
        ordering = ['-created_at']

    def __str__(self):
        local_created_at = timezone.localtime(self.created_at)
        formatted_time = local_created_at.strftime('%Y-%m-%d %H:%M')
        return f"{self.plant.name} - {self.get_event_type_display()} ({formatted_time})"
