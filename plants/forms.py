from django import forms
from .models import Plant, PlantLog

class PlantForm(forms.ModelForm):
    """
    화분 등록 및 수정을 위한 Django ModelForm 클래스입니다.
    부트스트랩/Vanilla CSS 클래스 적용 및 한글 라벨을 커스터마이징합니다.
    """
    class Meta:
        model = Plant
        # 2단계 보완: fields 순서 변경 (season 삭제, tip 추가)
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
    기존 WaterLog에서 통합 로그 모델인 PlantLog 대상으로 변경되었습니다.
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
