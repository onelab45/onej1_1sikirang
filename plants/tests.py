from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from .models import Plant, PlantLog
import datetime

class PlantModelTests(TestCase):
    """
    Plant 모델의 비즈니스 로직(D-Day, 오늘 예상 무게, 다음 물주기 예정일, 자동 로그 생성)을 검증하는 테스트 클래스입니다.
    """
    
    def setUp(self):
        # 테스트용 데이터 준비: 기준 시각을 현재로부터 정확히 2일 전으로 설정
        self.last_measured = timezone.now() - datetime.timedelta(days=2)
        
        # 2단계 보완: season 삭제, tip 추가
        self.plant = Plant.objects.create(
            name="몬스테라",
            current_weight=500.0,
            daily_decrease=10.0,
            water_threshold=400.0,
            tip="봄에는 지지대 필요",
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

    def test_tip_field_storage(self):
        """
        tip 필드가 데이터베이스에 잘 저장되고 조회되는지 확인합니다.
        """
        retrieved_plant = Plant.objects.get(pk=self.plant.pk)
        self.assertEqual(retrieved_plant.tip, "봄에는 지지대 필요")

    def test_plant_log_created_on_creation(self):
        """
        [a] 화분 생성(등록) 시 PlantLog가 자동으로 생성되는지 검증합니다.
        """
        # setUp에서 이미 화분을 1개 등록하였으므로 로그 개수가 1개여야 합니다.
        log = self.plant.logs.first()
        self.assertIsNotNone(log)
        self.assertEqual(log.event_type, 'created')
        self.assertIn("초기값:", log.detail)
        self.assertIn("Tip: 봄에는 지지대 필요", log.detail)

    def test_plant_log_updated_on_modification(self):
        """
        [c] 설정 변경 시 변경 내역이 포함된 PlantLog가 자동으로 생성되는지 검증합니다.
        """
        # 설정 변경
        self.plant.name = "몬스테라_수정"
        self.plant.daily_decrease = 12.0
        self.plant.tip = "지지대 추가 완료"
        self.plant.save()
        
        # 로그 확인 (등록 로그 1개 + 수정 로그 1개 = 총 2개)
        logs = self.plant.logs.all().order_by('-created_at')
        self.assertEqual(logs.count(), 2)
        
        latest_log = logs.first()
        self.assertEqual(latest_log.event_type, 'updated')
        self.assertIn("이름: 몬스테라 → 몬스테라_수정", latest_log.detail)
        self.assertIn("1일 감소량: 10.0g → 12.0g", latest_log.detail)
        self.assertIn('Tip 변경: "봄에는 지지대 필요" → "지지대 추가 완료"', latest_log.detail)

    def test_plant_log_watered(self):
        """
        [b] 물주기 처리 시 PlantLog(watered)가 정상적으로 수동/자동 구분되어 기록되는지 검증합니다.
        """
        # views.py의 plant_water 동작 모사
        new_weight = 550.0
        now_time = timezone.now()
        
        # 1) 물주기 로그 직접 생성
        water_log = PlantLog.objects.create(
            plant=self.plant,
            event_type='watered',
            weight_after=new_weight,
            detail=f"물 준 후 무게: {new_weight}g / 메모: 흠뻑 줌",
            created_at=now_time
        )
        
        # 2) 플랜트 정보 업데이트 (_is_watering=True)
        self.plant._is_watering = True
        self.plant.current_weight = water_log.weight_after
        self.plant.last_measured_at = water_log.created_at
        self.plant.save()
        
        # 전체 로그 수 확인 (등록 로그 1개 + 물주기 로그 1개 = 총 2개)
        # 중복으로 설정 변경(updated) 로그가 남지 않았어야 합니다.
        logs = self.plant.logs.all().order_by('-created_at')
        self.assertEqual(logs.count(), 2)
        
        latest_log = logs.first()
        self.assertEqual(latest_log.event_type, 'watered')
        self.assertEqual(latest_log.weight_after, 550.0)
        self.assertIn("메모: 흠뻑 줌", latest_log.detail)
        
        # 550g 기준 물주기 잔여일 검증: (550 - 400)/10 = 15일 남음
        self.assertEqual(self.plant.days_until_watering, 15)


class PlantViewTests(TestCase):
    """
    각 페이지 뷰들의 정상 응답(HTTP 200) 및 리다이렉션을 검증합니다.
    """
    
    def setUp(self):
        # 2단계 보완: season 삭제
        self.plant = Plant.objects.create(
            name="스투키",
            current_weight=800.0,
            daily_decrease=8.0,
            water_threshold=700.0,
            tip="그늘진 곳에 두기",
            last_measured_at=timezone.now()
        )

    def test_home_view(self):
        response = self.client.get(reverse('plants:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "스투키")
        self.assertContains(response, "그늘진 곳에 두기")

    def test_plant_detail_view(self):
        response = self.client.get(reverse('plants:plant_detail', args=[self.plant.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "스투키")
        # 통합 이력에 "화분 등록" 문구가 노출되는지 검증
        self.assertContains(response, "화분 등록")

    def test_plant_create_view_get(self):
        response = self.client.get(reverse('plants:plant_create'))
        self.assertEqual(response.status_code, 200)

    def test_calendar_view(self):
        response = self.client.get(reverse('plants:calendar'))
        self.assertEqual(response.status_code, 200)
