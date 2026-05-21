from django import forms
from django.core.exceptions import ValidationError
from .models import Plant, PlantLog, UserProfile
import re

def validate_nickname(value):
    """
    닉네임 유효성 검사: 2~20자, 한글/영문/숫자/공백/괄호 허용
    """
    if len(value) < 2 or len(value) > 20:
        raise ValidationError("닉네임은 2자 이상 20자 이하로 입력해 주세요.")
    
    # 한글(가-힣), 영문(a-zA-Z), 숫자(0-9), 공백(\s), 괄호(())만 허용하는 정규식
    if not re.match(r'^[a-zA-Z0-9가-힣\s()]+$', value):
        raise ValidationError("닉네임에는 한글, 영문, 숫자, 공백, 괄호만 사용할 수 있습니다.")

def validate_pin(value):
    """
    PIN 유효성 검사: 정확히 4자리 숫자
    """
    if not re.match(r'^\d{4}$', value):
        raise ValidationError("PIN 번호는 정확히 4자리 숫자여야 합니다.")


class LoginForm(forms.Form):
    """
    로그인을 위한 Form 클래스입니다.
    """
    nickname = forms.CharField(
        max_length=20,
        validators=[validate_nickname],
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '닉네임을 입력하세요',
            'required': 'required'
        }),
        label="닉네임"
    )
    pin = forms.CharField(
        max_length=4,
        min_length=4,
        validators=[validate_pin],
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'PIN 번호 4자리',
            'required': 'required',
            'pattern': '[0-9]{4}',
            'inputmode': 'numeric'
        }),
        label="PIN 번호 (4자리)"
    )


class SignupForm(forms.Form):
    """
    회원가입을 위한 Form 클래스입니다.
    """
    nickname = forms.CharField(
        max_length=20,
        validators=[validate_nickname],
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '닉네임을 입력하세요',
            'required': 'required'
        }),
        label="닉네임"
    )
    pin = forms.CharField(
        max_length=4,
        min_length=4,
        validators=[validate_pin],
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'PIN 번호 4자리',
            'required': 'required',
            'pattern': '[0-9]{4}',
            'inputmode': 'numeric'
        }),
        label="PIN 번호 (4자리)"
    )
    pin_confirm = forms.CharField(
        max_length=4,
        min_length=4,
        validators=[validate_pin],
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'PIN 번호 확인 4자리',
            'required': 'required',
            'pattern': '[0-9]{4}',
            'inputmode': 'numeric'
        }),
        label="PIN 번호 확인"
    )

    def clean_nickname(self):
        """
        닉네임 중복 여부를 체크합니다.
        """
        nickname = self.cleaned_data.get('nickname')
        if UserProfile.objects.filter(nickname=nickname).exists():
            raise ValidationError("이미 사용 중인 닉네임이에요.")
        return nickname

    def clean(self):
        """
        PIN 번호와 PIN 확인 비밀번호가 서로 일치하는지 체크합니다.
        """
        cleaned_data = super().clean()
        pin = cleaned_data.get('pin')
        pin_confirm = cleaned_data.get('pin_confirm')

        if pin and pin_confirm and pin != pin_confirm:
            self.add_error('pin_confirm', "PIN 번호가 서로 일치하지 않아요.")
        return cleaned_data


class PlantForm(forms.ModelForm):
    """
    화분 등록 및 수정을 위한 Django ModelForm 클래스입니다.
    """
    class Meta:
        model = Plant
        fields = ['name', 'current_weight', 'daily_decrease', 'water_threshold', 'tip']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': '예: 몬스테라, 스투키'
            }),
            'current_weight': forms.NumberInput(attrs={
                'class': 'form-input', 
                'placeholder': '현재 화분 무게(g)',
                'step': '0.1'
            }),
            'daily_decrease': forms.NumberInput(attrs={
                'class': 'form-input', 
                'placeholder': '하루 평균 무게 감소량(g)',
                'step': '0.1'
            }),
            'water_threshold': forms.NumberInput(attrs={
                'class': 'form-input', 
                'placeholder': '물을 주어야 하는 임계 무게(g)',
                'step': '0.1'
            }),
            'tip': forms.Textarea(attrs={
                'class': 'form-input', 
                'placeholder': '예: 봄에는 잎지지대 필요, 직사광선 피하기',
                'rows': 3
            }),
        }
        labels = {
            'name': '화분 이름',
            'current_weight': '최초/현재 무게 (g)',
            'daily_decrease': '1일 감소량 (g)',
            'water_threshold': '물주는 무게 (g)',
            'tip': '관리 Tip (선택)',
        }


class WaterForm(forms.ModelForm):
    """
    "물 줬어요" 기록 작성을 위한 Form 클래스입니다.
    """
    class Meta:
        model = PlantLog
        fields = ['weight_after', 'detail']
        widgets = {
            'weight_after': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '물 준 후 화분 무게(g)',
                'step': '0.1',
                'required': 'required'
            }),
            'detail': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '특이사항 메모 (선택)'
            }),
        }
        labels = {
            'weight_after': '물 준 후 무게 (g)',
            'detail': '메모',
        }
