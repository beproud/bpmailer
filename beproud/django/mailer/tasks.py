#:coding=utf-8:

try:
    # NOTE: ちゃんと設定が読み込まれるようにdjceleryをインポートする
    # TODO: Celery 3.1以上の場合 djcelery は必要ないので、その場合の対応をする
    import djcelery  # NOQA
except ImportError:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("djcelery is required!")

from django.conf import settings

try:
    from celery.task import task
except ImportError:
    raise ImproperlyConfigured("bpmailer tasks require celery to be installed!")

if 'djcelery' not in settings.INSTALLED_APPS:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("djcelery not in INSTALLED_APPS!")


from beproud.django.mailer import api as mailer_api

__all__ = (
    'send_mail',
    'send_template_mail',
    'send_mass_mail',
    'mail_managers',
    'mail_managers_template',
    'mail_admins',
)


@task
def send_mail(*args, **kwargs):
    max_retries = kwargs.pop('max_retries', 3)
    retry_countdown = kwargs.pop('retry_countdown', 10)
    try:
        mailer_api.send_mail(*args, **kwargs)
    except Exception, e:
        return send_mail.retry(
            exc=e,
            countdown=retry_countdown,
            max_retries=max_retries,
        )


@task
def send_template_mail(*args, **kwargs):
    max_retries = kwargs.pop('max_retries', 3)
    retry_countdown = kwargs.pop('retry_countdown', 10)
    try:
        mailer_api.send_template_mail(*args, **kwargs)
    except Exception, e:
        return send_template_mail.retry(
            exc=e,
            countdown=retry_countdown,
            max_retries=max_retries,
        )


@task
def send_mass_mail(*args, **kwargs):
    max_retries = kwargs.pop('max_retries', 3)
    retry_countdown = kwargs.pop('retry_countdown', 10)
    try:
        mailer_api.send_mass_mail(*args, **kwargs)
    except Exception, e:
        return send_mass_mail.retry(
            exc=e,
            countdown=retry_countdown,
            max_retries=max_retries,
        )


@task
def mail_managers(*args, **kwargs):
    max_retries = kwargs.pop('max_retries', 3)
    retry_countdown = kwargs.pop('retry_countdown', 10)
    try:
        mailer_api.mail_managers(*args, **kwargs)
    except Exception, e:
        return mail_managers.retry(
            exc=e,
            countdown=retry_countdown,
            max_retries=max_retries,
        )


@task
def mail_managers_template(*args, **kwargs):
    max_retries = kwargs.pop('max_retries', 3)
    retry_countdown = kwargs.pop('retry_countdown', 10)
    try:
        mailer_api.mail_managers_template(*args, **kwargs)
    except Exception, e:
        return mail_managers_template.retry(
            exc=e,
            countdown=retry_countdown,
            max_retries=max_retries,
        )


@task
def mail_admins(*args, **kwargs):
    max_retries = kwargs.pop('max_retries', 3)
    retry_countdown = kwargs.pop('retry_countdown', 10)
    try:
        mailer_api.mail_admins(*args, **kwargs)
    except Exception, e:
        return mail_admins.retry(
            exc=e,
            countdown=retry_countdown,
            max_retries=max_retries,
        )
