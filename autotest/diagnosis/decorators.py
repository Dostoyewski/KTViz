from threading import Thread


def postpone(function):
    """
    Decorator for multitasking
    :param function:
    :return:
    """

    def decorator(*args, **kwargs):
        t = Thread(target=function, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()

    return decorator
