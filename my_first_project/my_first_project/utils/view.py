from django.http import JsonResponse



def my_decorator(my_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'code':400,
                'errmsg':'请登录后重试'
            })
        result = my_func(request, *args, **kwargs)
        return result

    return wrapper

class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return my_decorator(view)
