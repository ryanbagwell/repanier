# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template
from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from repanier.const import EMPTY_STRING, PERMANENCE_CLOSED, DECIMAL_ZERO
from repanier.models import PermanenceBoard, CustomerInvoice
from repanier.tools import sint

register = template.Library()


@register.simple_tag(takes_context=False)
def repanier_home(*args, **kwargs):
    from repanier.apps import REPANIER_SETTINGS_HOME_SITE
    return REPANIER_SETTINGS_HOME_SITE


@register.simple_tag(takes_context=True)
def repanier_user(context, *args, **kwargs):
    from repanier.apps import REPANIER_SETTINGS_INVOICE, REPANIER_SETTINGS_DISPLAY_WHO_IS_WHO

    request = context["request"]
    user = request.user
    if user.is_authenticated:
        p_permanence_id = sint(kwargs.get('permanence_id', -1))
        p_delivery_id = sint(kwargs.get('delivery_id', -1))
        nodes = ["""
            <li id="li_my_name" class="dropdown">
            <a href="#" class="dropdown-toggle" data-toggle="dropdown"><span class="glyphicon glyphicon-user" aria-hidden="true"></span> %s %s<b class="caret"></b></a>
            <ul class="dropdown-menu">
            """ % (
            _('Welkom'),
            user.username or '<span id = "my_name"></ span>'
        )]
        if not user.is_staff:

            nodes.append('<li><a href="%s">%s</a></li>' % (
                reverse('send_mail_to_coordinators_view'),
                _('Send mail to coordinators')
            ))
            if REPANIER_SETTINGS_DISPLAY_WHO_IS_WHO:
                nodes.append('<li><a href="%s">%s</a></li>' % (
                    reverse('send_mail_to_all_members_view'),
                    _('Send mail to all members')
                ))
                nodes.append('<li><a href="%s">%s</a></li>' % (
                    reverse('who_is_who_view'),
                    _('Who is who')
                ))
            nodes.append('<li><a href="%s">%s</a></li>' % (
                reverse('my_profile_view'),
                _('My profile')
            ))
            if REPANIER_SETTINGS_INVOICE and not request.user.is_staff:
                last_customer_invoice = CustomerInvoice.objects.filter(
                    customer__user_id=request.user.id,
                    invoice_sort_order__isnull=False) \
                    .only("balance", "date_balance") \
                    .order_by('-invoice_sort_order').first()
                if last_customer_invoice is not None:
                    if last_customer_invoice.balance < DECIMAL_ZERO:
                        my_balance = _('My balance : <font color="red">%(balance)s</font> at %(date)s') % {
                            'balance': last_customer_invoice.balance,
                            'date'   : last_customer_invoice.date_balance.strftime(settings.DJANGO_SETTINGS_DATE)}
                    else:
                        my_balance = _('My balance : <font color="green">%(balance)s</font> at %(date)s') % {
                            'balance': last_customer_invoice.balance,
                            'date'   : last_customer_invoice.date_balance.strftime(settings.DJANGO_SETTINGS_DATE)}
                else:
                    my_balance = _('My balance')
                nodes.append('<li><a href="%s">%s</a></li>' % (
                    reverse("customer_invoice_view", args=(0,)),
                    my_balance
                ))
            nodes.append('<li class="divider"></li>')
        nodes.append('<li><a href="%s">%s</a></li>' % (
            reverse("logout_form"), _("Logout")
        ))
        nodes.append('</ul></li>')
        if p_permanence_id > 0:
            nodes.append('<li id="li_my_basket" style="display:none;" class="dropdown">')
            if p_delivery_id > 0:
                nodes.append('<a href="%s" class="btn btn-info"><span id="my_basket"></span></a>' %
                    reverse("basket_delivery_view", args=(p_permanence_id, p_delivery_id))
                )
            else:
                nodes.append('<a href="%s" class="btn btn-info"><span id="my_basket"></span></a>' %
                             reverse("basket_view", args=(p_permanence_id,))
                )
            nodes.append('</li>')
    else:
        nodes = ['<li class="dropdown"><a href="%s">%s</a></li>' % (
                reverse("login_form"),
                _("Login")
        )]

    return mark_safe("".join(nodes))


@register.simple_tag(takes_context=False)
def repanier_display_languages(*args, **kwargs):
    from django.conf import settings
    if len(settings.LANGUAGES) > 1:
        return "yes"
    return


@register.simple_tag(takes_context=False)
def repanier_display_task(*args, **kwargs):
    result = EMPTY_STRING
    p_permanence_board_id = sint(kwargs.get('permanence_board_id', 0))
    if p_permanence_board_id > 0:
        permanence_board = PermanenceBoard.objects.filter(id=p_permanence_board_id).select_related(
            "permanence_role"
        ).order_by('?').first()
        if permanence_board is not None:
            if permanence_board.permanence_role.customers_may_register:
                result = permanence_board.permanence_role
            else:
                result = '<p><b>%s</b></p>' % (permanence_board.permanence_role,)
    return mark_safe(result)


@register.simple_tag(takes_context=True)
def repanier_select_task(context, *args, **kwargs):
    request = context['request']
    user = request.user
    result = EMPTY_STRING
    if user.is_staff or user.is_superuser:
        pass
    else:
        p_permanence_board_id = sint(kwargs.get('permanence_board_id', 0))
        if p_permanence_board_id > 0:
            permanence_board = PermanenceBoard.objects.filter(id=p_permanence_board_id).select_related(
                "customer", "permanence_role", "permanence"
            ).order_by('?').first()
            if permanence_board is not None:
                if permanence_board.customer is not None:
                    if permanence_board.customer.user_id == user.id and permanence_board.permanence.status <= PERMANENCE_CLOSED:
                        result = """
                        <b><i>
                        <select name="value" id="permanence_board{permanence_board_id}"
                        onchange="permanence_board_ajax({permanence_board_id})" class="form-control">
                        <option value="0">---</option>
                        <option value="1" selected>{long_basket_name}</option>
                        </select>
                        </i></b>
                        """.format(
                            permanence_board_id=permanence_board.id,
                            long_basket_name=user.customer.long_basket_name
                        )
                    else:
                        result = """
                        <select name="value" id="permanence_board{permanence_board_id}"
                        class="form-control">
                        <option value="0" selected>{long_basket_name}</option>
                        </select>
                        """.format(
                            permanence_board_id=permanence_board.id,
                            long_basket_name=permanence_board.customer.long_basket_name
                        )
                else:
                    if permanence_board.permanence_role.customers_may_register:
                        if permanence_board.permanence.status <= PERMANENCE_CLOSED:
                            result = """
                            <b><i>
                            <select name="value" id="permanence_board{permanence_board_id}"
                            onchange="permanence_board_ajax({permanence_board_id})" class="form-control">
                            <option value="0" selected>---</option>
                            <option value="1">{long_basket_name}</option>
                            </select>
                            </i></b>
                            """.format(
                                permanence_board_id=permanence_board.id,
                                long_basket_name=user.customer.long_basket_name
                            )
                        else:
                            result = """
                            <select name="value" id="permanence_board{permanence_board_id}"
                            class="form-control">
                            <option value="0" selected>---</option>
                            </select>
                            """.format(
                                permanence_board_id=permanence_board.id
                            )
    return mark_safe(result)
