import threading

_thread_local = threading.local()


def set_current_user(user):
    _thread_local.user = user


def get_current_user():
    return getattr(_thread_local, 'user', None)


def clear_current_user():
    _thread_local.user = None