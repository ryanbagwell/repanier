# -*- coding: utf-8 -*-
import datetime
import logging
import threading
import uuid

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger(__name__)

from repanier.const import *
from repanier.email import email_offer
from repanier.email import email_order
from repanier.models.box import Box
from repanier.models.deliveryboard import DeliveryBoard
from repanier.models.offeritem import OfferItemWoReceiver
from repanier.models.permanence import Permanence
from repanier.models.producer import Producer
from repanier.models.product import Product
from repanier.tools import reorder_offer_items
from repanier.tools import reorder_purchases


@transaction.atomic
def automatically_pre_open():
    translation.activate(settings.LANGUAGE_CODE)
    something_to_pre_open = False
    max_3_days_in_the_future = (timezone.now() + datetime.timedelta(days=3)).date()
    for permanence in Permanence.objects.filter(
            status=PERMANENCE_PLANNED,
            permanence_date__lte=max_3_days_in_the_future,
            automatically_closed=True):
        producers = list(Producer.objects.filter(
            is_active=True, producer_pre_opening=True
        ).values_list(
            'id', flat=True
        ).order_by('?'))
        permanence.producers.add(*producers)
        permanence.set_status(PERMANENCE_WAIT_FOR_PRE_OPEN)
        pre_open_order(permanence.id)
        something_to_pre_open = True
    return something_to_pre_open


@transaction.atomic
def automatically_open():
    translation.activate(settings.LANGUAGE_CODE)
    something_to_open = False
    for permanence in Permanence.objects.filter(
            status=PERMANENCE_PRE_OPEN,
            automatically_closed=True):
        permanence.set_status(PERMANENCE_WAIT_FOR_OPEN)
        open_order(permanence.id)
        something_to_open = True
    return something_to_open


def common_to_pre_open_and_open(permanence_id):
    permanence = Permanence.objects.filter(id=permanence_id).order_by('?').first()

    if permanence.contract is not None:
        permanence.contract.get_or_create_offer_item(permanence, reset_add_2_stock=True)
    else:
        # Create offer items which can be purchased depending on selection in the admin
        producers_in_this_permanence = Producer.objects.filter(
            permanence=permanence_id,
            is_active=True
        ).order_by('?').only("id")
        product_queryset = Product.objects.filter(
            producer__in=producers_in_this_permanence,
            is_box=False,
            is_into_offer=True
        ).order_by('?')
        for product in product_queryset:
            product.get_or_create_offer_item(permanence, reset_add_2_stock=True)
        boxes_in_this_permanence = Box.objects.filter(
            permanence=permanence_id,
            is_active=True
        ).order_by('?').only("id")
        for box in boxes_in_this_permanence:
            box.get_or_create_offer_item(permanence, reset_add_2_stock=True)
    # Calculate the sort order of the order display screen
    reorder_offer_items(permanence_id)
    # Calculate the Purchase 'sum' for each customer
    permanence.recalculate_order_amount()
    return permanence


@transaction.atomic
def pre_open_order(permanence_id):
    permanence = common_to_pre_open_and_open(permanence_id)
    # 1 - Allow access to the producer to his/her products into "pre order" status using random uuid4
    for producer in Producer.objects.filter(
            permanence=permanence_id, producer_pre_opening=True
    ).only('offer_uuid').order_by('?'):
        producer.offer_uuid = uuid.uuid1()
        producer.offer_filled = False
        producer.save(update_fields=['offer_uuid', 'offer_filled'])
    email_offer.send_pre_open_order(permanence_id)
    permanence.set_status(PERMANENCE_PRE_OPEN)


@transaction.atomic
def open_order(permanence_id, do_not_send_any_mail=False):
    permanence = common_to_pre_open_and_open(permanence_id)
    # 1 - Disallow access to the producer to his/her products no more into "pre order" status
    for producer in Producer.objects.filter(
            permanence=permanence_id,
            producer_pre_opening=True,
            is_active=True
    ).only('offer_uuid', 'offer_filled').order_by('?'):
        producer.offer_uuid = uuid.uuid1()
        producer.save(update_fields=['offer_uuid', ])
        if not producer.offer_filled:
            # Deactivate offer item if the producer as not reacted to the pre opening
            OfferItemWoReceiver.objects.filter(
                permanence_id=permanence_id,
                may_order=True,
                producer_id=producer.id
            ).update(may_order=False)
    # 3 - Keep only producer with offer items which can be ordered
    permanence.producers.clear()
    for offer_item in OfferItemWoReceiver.objects.filter(
            permanence_id=permanence.id,
            # order_unit__lt=PRODUCT_ORDER_UNIT_DEPOSIT,
            may_order=True
    ).order_by().distinct("producer_id"):
        permanence.producers.add(offer_item.producer_id)

    if not do_not_send_any_mail:
        email_offer.send_open_order(permanence_id)
    permanence.set_status(PERMANENCE_OPENED)


def admin_back_to_scheduled(request, permanence):
    permanence.producers.clear()
    for offer_item in OfferItemWoReceiver.objects.filter(
            permanence_id=permanence.id,
            may_order=True
    ).order_by().distinct("producer_id"):
        permanence.producers.add(offer_item.producer_id)
    OfferItemWoReceiver.objects.filter(permanence_id=permanence.id).update(may_order=False)
    permanence.set_status(PERMANENCE_PLANNED)
    user_message = _("The permanence is back to scheduled.")
    user_message_level = messages.INFO
    return user_message, user_message_level


def admin_open_and_send(request, permanence, do_not_send_any_mail=False):
    producer_pre_opening = Producer.objects.filter(
        permanence__id=permanence.id, is_active=True, producer_pre_opening=True
    ).order_by('?')
    if producer_pre_opening.exists() and permanence.status == PERMANENCE_PLANNED:
        permanence_already_pre_opened = Permanence.objects.filter(
            status__in=[PERMANENCE_WAIT_FOR_PRE_OPEN, PERMANENCE_PRE_OPEN]
        ).order_by("-is_updated_on").only("id").first()
        if permanence_already_pre_opened is not None:
            user_message = _("A maximum of one permanence may be pre opened.")
            user_message_level = messages.ERROR
        else:
            permanence.set_status(PERMANENCE_WAIT_FOR_PRE_OPEN)
            # pre_open_order(permanence.id)
            t = threading.Thread(target=pre_open_order, args=(permanence.id,))
            t.start()
            user_message = _("The offers are being generated.")
            user_message_level = messages.INFO
    else:
        permanence.set_status(PERMANENCE_WAIT_FOR_OPEN)
        # open_order(permanence.id, do_not_send_any_mail)
        t = threading.Thread(target=open_order, args=(permanence.id, do_not_send_any_mail))
        t.start()
        user_message = _("The offers are being generated.")
        user_message_level = messages.INFO
    return user_message, user_message_level


@transaction.atomic
def automatically_closed():
    translation.activate(settings.LANGUAGE_CODE)
    something_to_close = False
    for permanence in Permanence.objects.filter(
            status=PERMANENCE_OPENED,
            automatically_closed=True):
        if permanence.with_delivery_point:
            deliveries_id = list(DeliveryBoard.objects.filter(
                permanence_id=permanence.id,
                status=PERMANENCE_OPENED
            ).values_list('id', flat=True))
            producers_id=()
        else:
            deliveries_id = ()
            producers_id = list(Producer.objects.filter(
                producerinvoice__permanence_id=permanence.id,
                producerinvoice__status=PERMANENCE_OPENED
            ).values_list('id', flat=True))
        close_and_send_order(permanence.id, everything=True, producers_id=producers_id, deliveries_id=deliveries_id)
        something_to_close = True
    return something_to_close


# Important : no @transaction.atomic because otherwise the "clock" in **permanence.get_full_status_display()**
# won't works on the admin screen. The clock is based on the permanence.status state.
def close_and_send_order(permanence_id, everything=True, producers_id=(), deliveries_id=()):
    # Be careful : use permanece_id, deliveries_id, ... and not objects
    # for the "thread" processing

    logger.debug("close_and_send_order")
    logger.debug("permanence_id : %s", permanence_id)
    logger.debug("everything : %s", everything)
    logger.debug("producers_id : %s", producers_id)
    logger.debug("deliveries_id : %s", deliveries_id)

    permanence = Permanence.objects.filter(id=permanence_id, status=PERMANENCE_OPENED).order_by('?').first()
    if permanence is None:
        return
    if permanence.with_delivery_point:
        if len(deliveries_id) == 0:
            return
        if len(producers_id) > 0:
            return
    else:
        if len(deliveries_id) > 0:
            return
        if len(producers_id) == 0:
            return

        if not everything and settings.REPANIER_SETTINGS_CUSTOMER_MUST_CONFIRM_ORDER:
            return

    permanence.set_status(PERMANENCE_WAIT_FOR_CLOSED, everything=everything, producers_id=producers_id,
                          deliveries_id=deliveries_id)
    permanence.close_order(everything=everything, producers_id=producers_id, deliveries_id=deliveries_id)
    permanence.set_status(PERMANENCE_CLOSED, everything=everything, producers_id=producers_id,
                          deliveries_id=deliveries_id)
    permanence.set_status(PERMANENCE_WAIT_FOR_SEND, everything=everything, producers_id=producers_id,
                          deliveries_id=deliveries_id)
    permanence.recalculate_order_amount(send_to_producer=True)
    reorder_purchases(permanence.id)
    email_order.email_order(permanence.id, everything=everything, producers_id=producers_id,
                            deliveries_id=deliveries_id)
    permanence.set_status(PERMANENCE_SEND, everything=everything, producers_id=producers_id,
                          deliveries_id=deliveries_id)


def admin_close_and_send_order(permanence_id, everything=True, producers_id=(), deliveries_id=()):
    # close_and_send_order(permanence_id, everything, producers_id, deliveries_id)
    t = threading.Thread(target=close_and_send_order,
                         args=(permanence_id, everything, producers_id, deliveries_id))
    t.start()
    user_message = _("The orders are being send.")
    user_message_level = messages.INFO
    return user_message, user_message_level
