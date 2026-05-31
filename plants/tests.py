from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from .models import Plant, PlantLog, UserProfile
import datetime

class PlantModelTests(TestCase):
    """
    Plant 모델의 비즈니스 로직(D-Day, 오늘 예상 무게, 다음 물주기 예정일, 자동 로그 생성)을 검증하는 테스트 클래스입니다.
    """
    
    def setUp(self):
        # 테스트용 사용자 생성
        self.user = UserProfile.objects.create(nickname="민우")
        self.user.set_pin("1234")
        self.user.save()
        
        # 테스트용 데이터 준비: 기준 시각을 현재로부터 정확히 2일 전으로 설정
        self.last_measured = timezone.now() - datetime.timedelta(days=2)
        
        # user 외래키 지정 연동
        self.plant = Plant.objects.create(
            user=self.user,
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
        self.assertAlmostEqual(self.plant.estimated_weight_today, 480.0, places=1)

    def test_watering_date(self):
        """
        다음 물주기 예정일이 마지막 측정 시각(2일 전)으로부터 10일 후(현재 시점 기준 8일 후)인지 확인합니다.
        """
        expected_date = timezone.localtime(self.last_measured).date() + datetime.timedelta(days=10)
        self.assertEqual(self.plant.watering_date, expected_date)

    def test_days_until_watering(self):
        """
        현재 시점 기준으로 다음 물주기까지 남은 일수가 8일인지 확인합니다.
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
        log = self.plant.logs.first()
        self.assertIsNotNone(log)
        self.assertEqual(log.event_type, 'created')
        self.assertIn("초기값:", log.detail)
        self.assertIn("Tip: 봄에는 지지대 필요", log.detail)

    def test_plant_log_updated_on_modification(self):
        """
        [c] 설정 변경 시 변경 내역이 포함된 PlantLog가 자동으로 생성되는지 검증합니다.
        """
        self.plant.name = "몬스테라_수정"
        self.plant.daily_decrease = 12.0
        self.plant.tip = "지지대 추가 완료"
        self.plant.save()
        
        logs = self.plant.logs.all().order_by('-created_at')
        self.assertEqual(logs.count(), 2)
        
        latest_log = logs.first()
        self.assertEqual(latest_log.event_type, 'updated')
        self.assertIn("이름: 몬스테라 → 몬스테라_수정", latest_log.detail)
        self.assertIn("1일 감소량: 10.0g → 12.0g", latest_log.detail)
        self.assertIn('Tip 변경: "봄에는 지지대 필요" → "지지대 추가 완료"', latest_log.detail)

    def test_plant_log_watered(self):
        """
        [b] 물주기 처리 시 PlantLog(watered)가 정상적으로 기록되는지 검증합니다.
        """
        new_weight = 550.0
        now_time = timezone.now()
        
        water_log = PlantLog.objects.create(
            plant=self.plant,
            event_type='watered',
            weight_after=new_weight,
            detail=f"물 준 후 무게: {new_weight}g / 메모: 흠뻑 줌",
            created_at=now_time
        )
        
        self.plant._is_watering = True
        self.plant.current_weight = water_log.weight_after
        self.plant.last_measured_at = water_log.created_at
        self.plant.save()
        
        logs = self.plant.logs.all().order_by('-created_at')
        self.assertEqual(logs.count(), 2)
        
        latest_log = logs.first()
        self.assertEqual(latest_log.event_type, 'watered')
        self.assertEqual(latest_log.weight_after, 550.0)
        self.assertIn("메모: 흠뻑 줌", latest_log.detail)


class UserProfileModelTests(TestCase):
    """
    UserProfile 모델의 비밀번호 해싱 및 매칭 검증을 다루는 테스트 클래스입니다.
    """
    
    def test_create_user_and_check_pin(self):
        user = UserProfile.objects.create(nickname="철수")
        user.set_pin("4321")
        user.save()
        
        # PIN이 평문으로 저장되지 않았는지(해싱되었는지) 검증
        self.assertNotEqual(user.pin_hash, "4321")
        self.assertTrue(user.pin_hash.startswith("pbkdf2_sha256$"))
        
        # 올바른 PIN 대조 성공 확인
        self.assertTrue(user.check_pin("4321"))
        # 잘못된 PIN 대조 실패 확인
        self.assertFalse(user.check_pin("0000"))


class SikirangSecurityTests(TestCase):
    """
    로그인 세션 기반 데이터 격리 및 페이지 보호 등 보안 정책을 검증하는 테스트 클래스입니다.
    """
    
    def setUp(self):
        # 두 명의 테스트 사용자 생성
        self.user_a = UserProfile.objects.create(nickname="사용자A")
        self.user_a.set_pin("1111")
        self.user_a.save()
        
        self.user_b = UserProfile.objects.create(nickname="사용자B")
        self.user_b.set_pin("2222")
        self.user_b.save()
        
        # 사용자A의 화분 생성
        self.plant_a = Plant.objects.create(
            user=self.user_a,
            name="사용자A의스투키",
            current_weight=500.0,
            daily_decrease=5.0,
            water_threshold=400.0
        )
        
        # 사용자B의 화분 생성
        self.plant_b = Plant.objects.create(
            user=self.user_b,
            name="사용자B의선인장",
            current_weight=300.0,
            daily_decrease=2.0,
            water_threshold=250.0
        )

    def test_anonymous_redirect_to_login(self):
        """
        로그인하지 않은 상태로 홈 및 기타 보호 페이지 접근 시 로그인 화면으로 리다이렉트 되는지 확인합니다.
        """
        response = self.client.get(reverse('plants:home'))
        self.assertRedirects(response, reverse('plants:login'))
        
        response2 = self.client.get(reverse('plants:calendar'))
        self.assertRedirects(response2, reverse('plants:login'))

    def test_user_a_cannot_see_user_b_plants(self):
        """
        사용자A가 로그인했을 때 사용자B의 화분이 홈 목록에 보이지 않는지 검증합니다.
        """
        # 사용자A 로그인 시뮬레이션
        session = self.client.session
        session['user_id'] = self.user_a.id
        session['user_nickname'] = self.user_a.nickname
        session.save()
        
        response = self.client.get(reverse('plants:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "사용자A의스투키")
        self.assertNotContains(response, "사용자B의선인장")

    def test_user_a_cannot_access_user_b_plant_detail_directly(self):
        """
        사용자A가 사용자B의 화분 상세 페이지 ID를 강제로 쳐서 들어왔을 때, 404 에러를 반환하는지 검증합니다.
        """
        # 사용자A 로그인 시뮬레이션
        session = self.client.session
        session['user_id'] = self.user_a.id
        session['user_nickname'] = self.user_a.nickname
        session.save()
        
        # 사용자B의 화분 상세 페이지에 접근 시도
        response = self.client.get(reverse('plants:plant_detail', args=[self.plant_b.pk]))
        # 보안 규칙 준수: 타인 리소스 조회 시 404 리턴 검증
        self.assertEqual(response.status_code, 404)


class PlantViewTests(TestCase):
    """
    일반적인 뷰들의 응답을 검증하는 테스트 클래스입니다.
    """
    
    def setUp(self):
        self.user = UserProfile.objects.create(nickname="영희")
        self.user.set_pin("5678")
        self.user.save()
        
        # 테스트 로그인 처리
        session = self.client.session
        session['user_id'] = self.user.id
        session['user_nickname'] = self.user.nickname
        session.save()
        
        self.plant = Plant.objects.create(
            user=self.user,
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
        self.assertContains(response, "화분 등록")

    def test_plant_create_view_get(self):
        response = self.client.get(reverse('plants:plant_create'))
        self.assertEqual(response.status_code, 200)

    def test_calendar_view(self):
        response = self.client.get(reverse('plants:calendar'))
        self.assertEqual(response.status_code, 200)

    def test_plant_edit_view_post(self):
        """
        화분 정보 수정(POST)이 뷰를 통해 정상 처리되고 리다이렉트되는지 검증합니다.
        """
        post_data = {
            'name': '스투키_수정',
            'current_weight': 810.0,
            'daily_decrease': 9.0,
            'water_threshold': 710.0,
            'tip': '햇빛 자주 쬐어주기'
        }
        response = self.client.post(
            reverse('plants:plant_edit', args=[self.plant.pk]),
            data=post_data
        )
        self.assertRedirects(response, reverse('plants:plant_detail', args=[self.plant.pk]))
        
        # 수정사항이 반영되었는지 DB 조회
        updated_plant = Plant.objects.get(pk=self.plant.pk)
        self.assertEqual(updated_plant.name, '스투키_수정')
        self.assertEqual(updated_plant.current_weight, 810.0)
        self.assertEqual(updated_plant.daily_decrease, 9.0)
        self.assertEqual(updated_plant.water_threshold, 710.0)
        self.assertEqual(updated_plant.tip, '햇빛 자주 쬐어주기')

