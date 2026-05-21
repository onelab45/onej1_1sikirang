from django.shortcuts import redirect
from functools import wraps

def login_required_custom(view_func):
    """
    커스텀 로그인 필수 데코레이터입니다.
    사용자의 세션에 'user_id'가 기록되어 있지 않다면 로그인 페이지로 리다이렉트합니다.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'user_id' not in request.session:
            return redirect('plants:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
