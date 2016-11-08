import os
import sys
import django


def main():
    """
    Standalone django model test with a 'memory-only-django-installation'.
    You can play with a django model without a complete django app installation.
    http://www.djangosnippets.org/snippets/1044/
    """
    import logging
    logging.basicConfig()

    os.environ["DJANGO_SETTINGS_MODULE"] = "django.conf.global_settings"
    from django.conf import global_settings

    global_settings.SECRET_KEY = "SECRET"
    global_settings.INSTALLED_APPS = (
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'beproud.django.mailer',
    )
    global_settings.DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

    if django.VERSION > (1, 8):
        global_settings.TEMPLATES = [
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [],
                'APP_DIRS': True,
                'OPTIONS': {
                    'context_processors': [
                        'django.template.context_processors.debug',
                        'django.template.context_processors.request',
                        'django.contrib.auth.context_processors.auth',
                        'django.contrib.messages.context_processors.messages',
                    ],
                },
            },
        ]

    # For Celery Tests
    global_settings.CELERY_ALWAYS_EAGER = True
    global_settings.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

    import celery
    if celery.VERSION >= (3, 1):
        app = celery.Celery()
        app.config_from_object('django.conf:settings')
        app.autodiscover_tasks(lambda: global_settings.INSTALLED_APPS)
    else:
        global_settings.INSTALLED_APPS += ('djcelery',)

    if django.VERSION > (1, 7):
        django.setup()

    from django.test.utils import get_runner
    test_runner = get_runner(global_settings)

    if django.VERSION > (1, 2):
        test_runner = test_runner()
        if django.VERSION > (1, 6):
            tests = ['beproud.django.mailer']
        else:
            tests = ['mailer']
        failures = test_runner.run_tests(tests)
    else:
        failures = test_runner(['mailer'], verbosity=1)

    sys.exit(failures)

if __name__ == '__main__':
    main()
