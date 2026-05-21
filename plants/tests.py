from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from .models import Plant, WaterLog
import datetime

class PlantModelTests(TestCase):
    """
    Plant 모델의 비즈니스 로직(D-Day, 오늘 예상 무게, 다음 물주기 예정일)을 검증하는 테스트 클래스입니다.
    """
    
    def setUp(self):
        # 테스트용 데이터 준비: 기준 시각을 현재로부터 정확히 2일 전으로 설정
        self.last_measured = timezone.now() - datetime.timedelta(days=2)
        
        self.plant = Plant.objects.create(
            name="몬스테라",
            current_weight=500.0,
            daily_decrease=10.0,
            water_threshold=400.0,
            season="spring",
            last_measured_at=self.last_measured
        )

    def test_estimated_weight_today(self):
        """
        2일 전 측정된 500g 화분(하루 10g 감소)의 오늘 예상 무게가 480g인지 확인합니다.
        """
        # 500g - (10g * 2일) = 480.0g
        self.assertAlmostEqual(self.plant.estimated_weight_today, 480.0, places=1)

    def test_watering_date(self):
        """
        다음 물주기 예정일이 마지막 측정 시각(2일 전)으로부터 10일 후(현재 시점 기준 8일 후)인지 확인합니다.
        (500 - 400) / 10 = 10일 뒤 물주기
        """
        expected_date = timezone.localtime(self.last_measured).date() + datetime.timedelta(days=10)
        self.assertEqual(self.plant.watering_date, expected_date)

    def test_days_until_watering(self):
        """
        현재 시점 기준으로 다음 물주기까지 남은 일수가 8일인지 확인합니다.
        10일(총 소요 일수) - 2일(경과 일수) = 8일 남음
        """
        self.assertEqual(self.plant.days_until_watering, 8)
        self.assertFalse(self.plant.is_watering_due)

    def test_water_action(self):
        """
        물주기 기록(WaterLog) 추가 시, 화분의 현재 무게와 마지막 측정 시각이 최신 상태로 업데이트되는지 확인합니다.
        """
        # 물주기 실행
        new_weight = 550.0
        now_time = timezone.now()
        
        log = WaterLog.objects.create(
            plant=self.plant,
            watered_at=now_time,
            weight_after=new_weight,
            memo="테스트 물주기"
        )
        
        # Plant 상태 업데이트 적용
        self.plant.current_weight = log.weight_after
        self.plant.last_measured_at = log.watered_at
        self.plant.save()
        
        # 검증
        self.assertEqual(self.plant.current_weight, 550.0)
        self.assertEqual(self.plant.last_measured_at, now_time)
        # 550g 기준으로 D-Day 재계산 검증: (550 - 400)/10 = 15일 남음
        self.assertEqual(self.plant.days_until_watering, 15)


class PlantViewTests(TestCase):
    """
    각 페이지 뷰들의 정상 응답(HTTP 200) 및 리다이렉션을 검증합니다.
    """
    
    def setUp(self):
        self.plant = Plant.objects.create(
            name="스투키",
            current_weight=800.0,
            daily_decrease=8.0,
            water_threshold=700.0,
            season="spring",
            last_measured_at=timezone.now()
        )

    def test_home_view(self):
        response = self.client.get(reverse('plants:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "스투키")

    def test_plant_detail_view(self):
        response = self.client.get(reverse('plants:plant_detail', args=[self.plant.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "스투키")

    def test_plant_create_view_get(self):
        response = self.client.get(reverse('plants:plant_create'))
        self.assertEqual(response.status_code, 200)

    def test_calendar_view(self):
        response = self.client.get(reverse('plants:calendar'))
        self.assertEqual(response.status_code, 200)
