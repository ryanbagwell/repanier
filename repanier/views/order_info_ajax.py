# -*- coding: utf-8
from __future__ import unicode_literals

from django.conf import settings
from django.http import Http404
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from repanier.const import PERMANENCE_OPENED, EMPTY_STRING
from repanier.models import Permanence


@never_cache
@require_GET
def order_info_ajax(request):
    if request.is_ajax():
        from repanier.apps import REPANIER_SETTINGS_CONFIG
        order_info = EMPTY_STRING
        if REPANIER_SETTINGS_CONFIG.notification:
            if REPANIER_SETTINGS_CONFIG.notification_is_public or request.user.is_authenticated:
                order_info = """
                <div class="row">
                    <div class="panel-group">
                        <div class="panel panel-default">
                            <div class="panel-body">
                                <div class="col-md-12">
                                {notification}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                """.format(
                    notification=REPANIER_SETTINGS_CONFIG.notification
                )

        return HttpResponse(order_info)
    raise Http404