SECRET_KEY = "SECRET"
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'beproud.django.mailer',
)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

TEMPLATES = [
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
USE_TZ = False

# For Celery Tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
BROKER_BACKEND = 'memory'

import celery

app = celery.Celery()
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: INSTALLED_APPS)
