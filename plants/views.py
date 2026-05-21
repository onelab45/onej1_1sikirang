from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Plant, PlantLog, UserProfile
from .forms import PlantForm, WaterForm, LoginForm, SignupForm
from .decorators import login_required_custom
import calendar
import datetime

def root_view(request):
    """
    루트 경로(/) 뷰:
    사용자가 로그인되어 있으면 홈 화면으로, 그렇지 않으면 로그인 화면으로 리다이렉트합니다.
    """
    if 'user_id' in request.session:
        return redirect('plants:home')
    return redirect('plants:login')


def login_view(request):
    """
    로그인 뷰:
    GET: 로그인 및 회원가입 폼이 병렬 구성된 페이지를 표시합니다.
    POST: 사용자가 입력한 닉네임과 PIN을 검증하여 로그인 처리를 수행합니다.
    """
    if 'user_id' in request.session:
        return redirect('plants:home')
        
    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        signup_form = SignupForm()
        
        if login_form.is_valid():
            nickname = login_form.cleaned_data['nickname']
            pin = login_form.cleaned_data['pin']
            try:
                user = UserProfile.objects.get(nickname=nickname)
                if user.check_pin(pin):
                    # 세션 로그인 처리
                    request.session['user_id'] = user.id
                    request.session['user_nickname'] = user.nickname
                    user.last_login_at = timezone.now()
                    user.save()
                    return redirect('plants:home')
                else:
                    login_form.add_error(None, "닉네임 또는 PIN이 맞지 않아요.")
            except UserProfile.DoesNotExist:
                login_form.add_error(None, "닉네임 또는 PIN이 맞지 않아요.")
                
        return render(request, 'plants/login.html', {
            'login_form': login_form,
            'signup_form': signup_form,
            'active_tab': 'login'
        })
    else:
        return render(request, 'plants/login.html', {
            'login_form': LoginForm(),
            'signup_form': SignupForm(),
            'active_tab': 'login'
        })


def signup_view(request):
    """
    회원가입 뷰 (POST 전용):
    입력 유효성 검사 후 새 UserProfile 인스턴스를 생성하고, PIN을 암호화하여 저장 후 자동 로그인 처리합니다.
    """
    if 'user_id' in request.session:
        return redirect('plants:home')
        
    if request.method == 'POST':
        signup_form = SignupForm(request.POST)
        login_form = LoginForm()
        
        if signup_form.is_valid():
            nickname = signup_form.cleaned_data['nickname']
            pin = signup_form.cleaned_data['pin']
            
            user = UserProfile(nickname=nickname)
            user.set_pin(pin)
            user.last_login_at = timezone.now()
            user.save()
            
            # 회원가입 성공 시 세션 로그인 처리
            request.session['user_id'] = user.id
            request.session['user_nickname'] = user.nickname
            return redirect('plants:home')
            
        return render(request, 'plants/login.html', {
            'login_form': login_form,
            'signup_form': signup_form,
            'active_tab': 'signup'
        })
    else:
        return redirect('plants:login')


def logout_view(request):
    """
    로그아웃 뷰:
    사용자 세션을 완전히 초기화한 후 로그인 페이지로 이동합니다.
    """
    request.session.flush()
    return redirect('plants:login')


@login_required_custom
def home(request):
    """
    홈 화면 뷰 (로그인 필수):
    현재 로그인된 사용자의 화분 목록을 조회하여 D-Day 순서로 정렬해 반환합니다.
    """
    current_user_id = request.session['user_id']
    # 로그인된 사용자의 화분만 필터링
    user_plants = list(Plant.objects.filter(user_id=current_user_id))
    
    # D-Day(물주기까지 남은 일수) 오름차순 정렬 (가장 급한 화분이 앞으로)
    sorted_plants = sorted(user_plants, key=lambda p: p.days_until_watering)
    
    context = {
        'plants': sorted_plants,
    }
    return render(request, 'plants/home.html', context)


@login_required_custom
def plant_create(request):
    """
    화분 등록 뷰 (로그인 필수):
    GET: 화분 등록 폼 페이지를 표시합니다.
    POST: 새 화분을 생성하고 소유 사용자를 설정하여 저장합니다.
    """
    current_user_id = request.session['user_id']
    user_profile = get_object_or_404(UserProfile, pk=current_user_id)
    
    if request.method == 'POST':
        form = PlantForm(request.POST)
        if form.is_valid():
            plant = form.save(commit=False)
            plant.user = user_profile
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


@login_required_custom
def plant_detail(request, pk):
    """
    화분 상세 조회 뷰 (로그인 필수, 본인 화분만 허용):
    GET: 상세 정보와 로그 이력을 표시하며, 수정 폼을 바인딩하여 렌더링합니다.
    """
    current_user_id = request.session['user_id']
    # 본인의 화분이 아닌 경우 보안상 404를 반환
    plant = get_object_or_404(Plant, pk=pk, user_id=current_user_id)
    
    form = PlantForm(instance=plant)
    water_form = WaterForm()
    water_logs = plant.logs.all().order_by('-created_at')
    
    context = {
        'plant': plant,
        'form': form,
        'water_form': water_form,
        'water_logs': water_logs,
    }
    return render(request, 'plants/plant_detail.html', context)


@login_required_custom
@require_POST
def plant_edit(request, pk):
    """
    화분 수정 처리 뷰 (로그인 필수, POST 전용, 본인 화분만 허용):
    """
    current_user_id = request.session['user_id']
    plant = get_object_or_404(Plant, pk=pk, user_id=current_user_id)
    
    form = PlantForm(request.POST, instance=plant)
    if form.is_valid():
        form.save()
    return redirect('plants:plant_detail', pk=plant.pk)


@login_required_custom
@require_POST
def plant_water(request, pk):
    """
    "물 줬어요" 처리 뷰 (로그인 필수, POST 전용, 본인 화분만 허용):
    """
    current_user_id = request.session['user_id']
    plant = get_object_or_404(Plant, pk=pk, user_id=current_user_id)
    form = WaterForm(request.POST)
    
    if form.is_valid():
        water_log = form.save(commit=False)
        water_log.plant = plant
        water_log.event_type = 'watered'
        
        detail_txt = f"물 준 후 무게: {water_log.weight_after}g"
        if water_log.detail:
            detail_txt += f" / 메모: {water_log.detail}"
        water_log.detail = detail_txt
        water_log.created_at = timezone.now()
        water_log.save()
        
        # Plant 모델의 현재 무게 및 마지막 측정 시각 동시 업데이트
        plant._is_watering = True
        plant.current_weight = water_log.weight_after
        plant.last_measured_at = water_log.created_at
        plant.save()
        
    return redirect('plants:plant_detail', pk=plant.pk)


@login_required_custom
@require_POST
def plant_delete(request, pk):
    """
    화분 삭제 뷰 (로그인 필수, POST 전용, 본인 화분만 허용):
    """
    current_user_id = request.session['user_id']
    plant = get_object_or_404(Plant, pk=pk, user_id=current_user_id)
    plant.delete()
    return redirect('plants:home')


@login_required_custom
def calendar_view(request):
    """
    월간 캘린더 뷰 (로그인 필수):
    로그인된 사용자의 화분들에 대해서만 일정을 노출합니다.
    """
    current_user_id = request.session['user_id']
    today = timezone.localdate()
    
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
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
        
    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdays2calendar(year, month)
    
    events = {}
    user_plants = Plant.objects.filter(user_id=current_user_id)
    for plant in user_plants:
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
