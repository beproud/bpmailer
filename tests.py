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
    global_settings.CELERY_TASK_ALWAYS_EAGER = True
    global_settings.CELERY_TASK_EAGER_PROPAGATES = True

    import celery
    app = celery.Celery()
    app.config_from_object('django.conf:settings', namespace='CELERY')
    app.autodiscover_tasks(lambda: global_settings.INSTALLED_APPS)

    django.setup()

    from django.test.utils import get_runner

    # Get a Django test runner class
    TestRunner = get_runner(global_settings)

    # Create a test runner object
    test_runner = TestRunner()

    # set 'bpmailer unit test path' and run the unit test
    failures = test_runner.run_tests(['beproud.django.mailer.tests'])

    sys.exit(failures)


if __name__ == '__main__':
    main()
