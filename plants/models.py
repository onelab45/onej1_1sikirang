from django.db import models
from django.utils import timezone
import datetime

# Create your models here.

class UserProfile(models.Model):
    """
    닉네임과 PIN 번호 해시를 관리하는 사용자 프로필 모델입니다.
    """
    nickname = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name="닉네임"
    )
    pin_hash = models.CharField(
        max_length=128, 
        verbose_name="PIN 해시"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="가입 일시"
    )
    last_login_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="최근 로그인 일시"
    )

    def set_pin(self, raw_pin):
        """
        입력된 PIN 번호를 Django의 make_password를 사용하여 안전하게 해싱 저장합니다.
        """
        from django.contrib.auth.hashers import make_password
        self.pin_hash = make_password(raw_pin)

    def check_pin(self, raw_pin):
        """
        해싱 저장된 PIN 번호와 사용자가 입력한 PIN 번호를 대조 검증합니다.
        """
        from django.contrib.auth.hashers import check_password
        return check_password(raw_pin, self.pin_hash)

    class Meta:
        verbose_name = "사용자 프로필"
        verbose_name_plural = "사용자 프로필 목록"
        ordering = ['-created_at']

    def __str__(self):
        return self.nickname


class Plant(models.Model):
    """
    화분 정보를 저장하는 모델입니다.
    각 화분의 소유 사용자(user), 현재 무게, 하루 물 감소량, 물을 주어야 하는 한계 무게, 관리 팁 등을 관리합니다.
    """
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='plants',
        verbose_name="소유 사용자"
    )
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
    calendar_event_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="구글 캘린더 이벤트 ID"
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
        now = timezone.now()
        delta = now - self.last_measured_at
        days_passed = delta.total_seconds() / 86400.0
        
        if days_passed < 0:
            days_passed = 0.0
            
        weight = self.current_weight - (self.daily_decrease * days_passed)
        return round(max(0.0, weight), 1)

    @property
    def days_until_watering(self):
        """
        물주기까지 남은 일수를 정수로 반환합니다. (음수 가능)
        공식: (물주기 예정일 - 오늘) 일수
        """
        today = timezone.localdate()
        w_date = self.watering_date
        return (w_date - today).days

    @property
    def watering_date(self):
        """
        물줘야 하는 예상 날짜(date 객체)를 계산하여 반환합니다.
        공식: 마지막 측정 시각 + ((현재 무게 - 물주는 무게) / 1일 감소량) 일
        """
        if self.daily_decrease <= 0:
            return timezone.localdate()
            
        days_to_threshold = (self.current_weight - self.water_threshold) / self.daily_decrease
        watering_datetime = self.last_measured_at + datetime.timedelta(days=days_to_threshold)
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
            super().save(*args, **kwargs)
            
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
            original = Plant.objects.get(pk=self.pk)
            changes = []
            
            if original.name != self.name:
                changes.append(f"이름: {original.name} → {self.name}")
                
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
                
            super().save(*args, **kwargs)
            
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
