from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Plant, PlantLog
from .forms import PlantForm, WaterForm
import calendar
import datetime

def home(request):
    """
    홈 화면 뷰:
    1) 모든 화분 목록을 조회합니다.
    2) 물주기가 임박한 화물(D-Day가 가장 낮거나 음수인 화분) 상위 2개를 알람 창에 노출합니다.
    """
    # 데이터베이스의 모든 화분 조회
    all_plants = list(Plant.objects.all())
    
    # D-Day(물주기까지 남은 일수) 오름차순으로 정렬 (가장 급한 화분이 앞으로)
    sorted_plants = sorted(all_plants, key=lambda p: p.days_until_watering)
    
    # 임박한 물주기 알람 2개 추출
    urgent_plants = sorted_plants[:2]
    
    context = {
        'plants': all_plants,
        'urgent_plants': urgent_plants,
    }
    return render(request, 'plants/home.html', context)


def plant_create(request):
    """
    화분 등록 뷰:
    GET: 신규 등록 폼 페이지를 표시합니다.
    POST: 입력값을 유효성 검사한 후, 새 Plant 인스턴스를 데이터베이스에 저장합니다.
          (마지막 측정 시각은 저장하는 현재 시각으로 자동 설정됩니다.)
    """
    if request.method == 'POST':
        form = PlantForm(request.POST)
        if form.is_valid():
            plant = form.save(commit=False)
            # 최초 등록 시점의 시각을 마지막 측정 시각으로 자동 기록
            plant.last_measured_at = timezone.now()
            plant.save()
            return redirect('plants:home')
    else:
        form = PlantForm()
        
    context = {
        'form': form,
        'title': '새 화분 등록',
    }
    return render(request, 'plants/plant_form.html', context)


def plant_detail(request, pk):
    """
    화분 상세/수정 뷰:
    GET: 화분의 오늘 예상 무게, D-Day 등의 정보와 물주기 이력 목록을 표시하며, 
         관리 메뉴(수정 폼)도 함께 제공합니다.
    POST: 수정 폼 제출 시 화분 세부 설정(Y, Z, 계절 등)을 갱신합니다.
    """
    plant = get_object_or_404(Plant, pk=pk)
    
    if request.method == 'POST':
        form = PlantForm(request.POST, instance=plant)
        if form.is_valid():
            form.save()
            return redirect('plants:plant_detail', pk=plant.pk)
    else:
        form = PlantForm(instance=plant)
        
    # 물주기 기록 폼 및 목록 데이터 준비 (WaterLog -> PlantLog)
    water_form = WaterForm()
    water_logs = plant.logs.all().order_by('-created_at')
    
    context = {
        'plant': plant,
        'form': form,
        'water_form': water_form,
        'water_logs': water_logs,
    }
    return render(request, 'plants/plant_detail.html', context)


@require_POST
def plant_water(request, pk):
    """
    "물 줬어요" 처리 뷰 (POST 방식 전용):
    물 준 후 무게와 메모를 기록하여 물주기 이력(PlantLog)을 새로 생성하고,
    화분(Plant)의 현재 무게와 마지막 측정 시각을 최신 상태로 갱신합니다.
    """
    plant = get_object_or_404(Plant, pk=pk)
    form = WaterForm(request.POST)
    
    if form.is_valid():
        water_log = form.save(commit=False)
        water_log.plant = plant
        water_log.event_type = 'watered'
        # 상세 내용에 물 준 후 무게와 메모를 기록
        detail_txt = f"물 준 후 무게: {water_log.weight_after}g"
        if water_log.detail:
            detail_txt += f" / 메모: {water_log.detail}"
        water_log.detail = detail_txt
        
        # 물 준 시각은 현재 시각으로 자동 설정
        water_log.created_at = timezone.now()
        water_log.save()
        
        # Plant 모델의 현재 무게 및 마지막 측정 시각 동시 업데이트
        # _is_watering 속성을 부여해 save() 시 무게 단독 수정 로그 생성을 스킵합니다.
        plant._is_watering = True
        plant.current_weight = water_log.weight_after
        plant.last_measured_at = water_log.created_at
        plant.save()
        
    return redirect('plants:plant_detail', pk=plant.pk)


@require_POST
def plant_delete(request, pk):
    """
    화분 삭제 뷰 (POST 방식 전용):
    데이터베이스에서 해당 화분을 영구히 삭제한 후 홈 화면으로 리다이렉트합니다.
    """
    plant = get_object_or_404(Plant, pk=pk)
    plant.delete()
    return redirect('plants:home')


def calendar_view(request):
    """
    월간 캘린더 뷰:
    이번 달의 캘린더 그리드를 빌드하고, 각 날짜별로 물줘야 하는 예정 화분들을 표시합니다.
    """
    today = timezone.localdate()
    
    # GET 파라미터에서 년도와 월을 받아오고, 없으면 현재 년도와 월로 기본값 설정
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
    # 이전 달 및 다음 달 링크 처리를 위한 계산
    if month == 1:
        prev_year = year - 1
        prev_month = 12
    else:
        prev_year = year
        prev_month = month - 1
        
    if month == 12:
        next_year = year + 1
        next_month = 1
    else:
        next_year = year
        next_month = month + 1
        
    # 일요일 시작으로 달력 빌드 (firstweekday=6)
    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdays2calendar(year, month)
    
    # 이번 달의 예상 물주기 일정 매핑: {일자(day): [화분1, 화분2, ...]}
    events = {}
    all_plants = Plant.objects.all()
    for plant in all_plants:
        w_date = plant.watering_date
        if w_date.year == year and w_date.month == month:
            events.setdefault(w_date.day, []).append(plant)
            
    context = {
        'weeks': weeks,
        'year': year,
        'month': month,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'events': events,
        'today_day': today.day if today.year == year and today.month == month else 0,
    }
    return render(request, 'plants/calendar.html', context)
