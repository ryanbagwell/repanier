# -*- coding: utf-8 -*-
from settings import *

import os
import sys
gettext = lambda s: s
PROJECT_PATH = os.path.split(os.path.abspath(os.path.dirname(__file__)))[0]
PROJECT_DIR = os.path.realpath(os.path.dirname(__file__))
os.sys.path.insert(0, os.path.dirname(PROJECT_DIR))

###################### I18N

TIME_ZONE = 'Europe/Brussels'
LANGUAGE_CODE = 'fr-BE'

###################### DEBUG

# Defined into /etc/uwsgi/apps-available/*.ini
DEBUG = True if os.getenv('DJANGO_SETTINGS_MODULE_DEBUG','') == 'True' else False
TEMPLATE_DEBUG = DEBUG

##################### Django & Django CMS
LANGUAGES = [
    ('fr', 'Français'),
    ('nl', 'Neederlands'),
    ('en', 'English'),
]

CMS_LANGUAGES = {
    'default': {
        'fallbacks': ['fr', 'en', 'nl'],
        'redirect_on_fallback':True,
        'public': False,
        'hide_untranslated': False,
    }
}

LOCALE_PATHS = (
    os.path.join(PROJECT_DIR, "locale"),
)

MIDDLEWARE_CLASSES = (
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', 
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'cms.middleware.page.CurrentPageMiddleware',
    'cms.middleware.user.CurrentUserMiddleware',      
    'cms.middleware.toolbar.ToolbarMiddleware',
    'cms.middleware.language.LanguageCookieMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.i18n',
    'django.core.context_processors.request',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'cms.context_processors.media',
    'sekizai.context_processors.sekizai',  
)

INSTALLED_APPS = (
    'django.contrib.sites',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.formtools',
    'djangocms_text_ckeditor', # note this needs to be above the 'cms' entry
    'cms',
    'mptt',
    'menus',
    'south',
    'sekizai',
    'djangocms_admin_style', # note this needs to be above 
                            # the 'django.contrib.admin' entry
    'django.contrib.admin',
    'cms.plugins.googlemap',
    'cms.plugins.link',
    'filer',
    'easy_thumbnails',
    'cmsplugin_filer_file',
    'cmsplugin_filer_folder',
    'cmsplugin_filer_image',
    'cmsplugin_filer_teaser',
    'cmsplugin_filer_video',
    'reversion',
) 

CMS_PERMISSION = False # When set to True, don't forget 'cms.middleware.user.CurrentUserMiddleware' 
CMS_PUBLIC_FOR = 'all'
CMS_SHOW_START_DATE = False
CMS_SHOW_END_DATE = False
CMS_SEO_FIELDS = False
CMS_URL_OVERWRITE = True
CMS_MENU_TITLE_OVERWRITE = True
CMS_REDIRECTS = True
LOGIN_URL = "/#loginRequired"
LOGIN_REDIRECT_URL = "/"
LOGOUT_URL = "/?cms-toolbar-logout"

CKEDITOR_SETTINGS = {
        'language': '{{ language }}',
        'toolbar': 'CMS2',
        'skin': 'moono',
        'toolbarCanCollapse' : False,
#        'stylesSet' : 'default:%sckeditor/styles.js' % STATIC_URL,
        'stylesSet' : 'my_styles:%sjs/ckeditor-styles.js' % STATIC_URL,
        'autoGrow_onStartup' :  True,
        'emailProtection' : '2',
        'toolbar_CMS2': [
                ['Undo', 'Redo'],
                ['cmsplugins'],
                # ['Format', '-','TextColor', 'BGColor', '-', 'Bold', 'Italic', 'Underline', '-', 
                ['Styles', '-','TextColor', 'Bold', 'Italic', '-', 'RemoveFormat', 'PasteText'],
                ['JustifyLeft', 'JustifyCenter', 'JustifyRight'],
                ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'Table'],
                ['Source'],['Maximize', '-', 'ShowBlocks'],
        ],
}

TEXT_SAVE_IMAGE_FUNCTION='cmsplugin_filer_image.integrations.ckeditor.create_image_plugin'

FILER_ENABLE_LOGGING = False
FILER_IMAGE_USE_ICON = True
FILER_ALLOW_REGULAR_USERS_TO_ADD_ROOT_FOLDERS = False
FILER_ENABLE_PERMISSIONS = True
FILER_IS_PUBLIC_DEFAULT = True
FILER_SUBJECT_LOCATION_IMAGE_DEBUG = True
FILER_DEBUG = DEBUG

THUMBNAIL_PROCESSORS = (
    'easy_thumbnails.processors.colorspace',
    'easy_thumbnails.processors.autocrop',
    #'easy_thumbnails.processors.scale_and_crop',
    'filer.thumbnail_processors.scale_and_crop_with_subject_location',
    'easy_thumbnails.processors.filters',
)
THUMBNAIL_DEBUG = DEBUG

STATIC_ROOT = os.path.join(PROJECT_DIR, "collect-static")
STATIC_URL = "/static/"
MEDIA_URL = "/media/"
USE_X_FORWARDED_HOST = True
SEND_BROKEN_LINK_EMAILS = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_ENGINE = "django.contrib.sessions.backends.file"
SESSION_COOKIE_HTTPONLY = True
SESSION_FILE_PATH = '/var/tmp/django_session'
SOUTH_TESTS_MIGRATE = DEBUG

##################### Repanier
AUTHENTICATION_BACKENDS = ('repanier.auth_backend.RepanierCustomBackend',)
INSTALLED_APPS += (
	'repanier',
)


################# Django_crispy_forms
INSTALLED_APPS += (
    'crispy_forms',
    'crispy_forms_foundation',
)

# CRISPY_TEMPLATE_PACK = "bootstrap3"
CRISPY_TEMPLATE_PACK = "foundation"
JSON_MODULE = 'ujson'

################# Django_compressor
INSTALLED_APPS += (
    'compressor',
)
##### From : django/conf/global_settings.py
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

STATICFILES_FINDERS += (
     'compressor.finders.CompressorFinder',
)

COMPRESS_ENABLED = True
COMPRESS_OUTPUT_DIR = "compressor"
COMPRESS_STORAGE = 'compressor.storage.GzipCompressorFileStorage'
COMPRESS_PARSER = "compressor.parser.HtmlParser"
COMPRESS_OFFLINE = False

    # COMPRESS_YUI_BINARY = "yui-compressor"
    # COMPRESS_CLOSURE_COMPILER_BINARY = "/usr/local/bin/node /usr/local/bin/uglifyjs"
    # COMPRESS_CLOSURE_COMPILER_ARGUMENTS = '--compress'

    # COMPRESS_CSS_FILTERS = [
    #    'compressor.filters.yui.YUICSSFilter',
    #    'compressor.filters.css_default.CssAbsoluteFilter',
    #    'compressor.filters.template.TemplateFilter'
    #    ]

    # COMPRESS_JS_FILTERS = [
    #    'compressor.filters.yui.YUIJSFilter',
    #     'compressor.filters.closure.ClosureCompilerFilter',
    #    'compressor.filters.jsmin.JSMinFilter',
    #    'compressor.filters.template.TemplateFilter'
    #    ]

    # COMPRESS_PRECOMPILERS = (
    #    ('text/coffeescript', 'coffee --compile --stdio'),
    #    ('text/less', 'lessc {infile} {outfile}'),
    #    ('text/x-sass', 'sass {infile} {outfile}'),
    #    ('text/x-scss', 'sass --scss {infile} {outfile}'),
    #    ('text/stylus', 'stylus < {infile} > {outfile}'),
    # )

###################### Django : Cache setup (https://docs.djangoproject.com/en/dev/topics/cache/)

CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 3000

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache',
        'TIMEOUT': 3000,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3
        }
    }
}

CMS_CACHE_DURATIONS = {
    'content' : 300, # default 60
    'menus' : 15, # default 3600
    'permissions' : 3600 # default: 3600
}
