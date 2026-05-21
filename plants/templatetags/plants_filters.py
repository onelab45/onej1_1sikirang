from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    딕셔너리에서 변수로 된 키의 값을 가져오기 위한 템플릿 필터입니다.
    사용법: {{ dictionary|get_item:key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, [])
    return []
