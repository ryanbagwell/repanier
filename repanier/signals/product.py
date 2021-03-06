import uuid

from django.conf import settings
from django.db.models import F
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from repanier.const import (
    PRODUCT_ORDER_UNIT_PC,
    PRODUCT_ORDER_UNIT_PC_PRICE_KG,
    PRODUCT_ORDER_UNIT_PC_PRICE_LT,
    PRODUCT_ORDER_UNIT_PC_PRICE_PC,
    DECIMAL_ZERO,
    PRODUCT_ORDER_UNIT_PC_KG,
    PRODUCT_ORDER_UNIT_DEPOSIT,
    PRODUCT_ORDER_UNIT_MEMBERSHIP_FEE,
    VAT_100,
    PRODUCT_ORDER_UNIT_KG,
    PRODUCT_ORDER_UNIT_LT,
    DECIMAL_ONE,
    LIMIT_ORDER_QTY_ITEM,
    THREE_DECIMALS,
)
from repanier.models import Product


@receiver(pre_save, sender=Product)
def product_pre_save(sender, **kwargs):
    product = kwargs["instance"]
    producer = product.producer

    if product.order_unit not in [
        PRODUCT_ORDER_UNIT_PC,
        PRODUCT_ORDER_UNIT_PC_PRICE_KG,
        PRODUCT_ORDER_UNIT_PC_PRICE_LT,
        PRODUCT_ORDER_UNIT_PC_PRICE_PC,
    ]:
        product.unit_deposit = DECIMAL_ZERO
    if product.order_unit == PRODUCT_ORDER_UNIT_PC:
        product.order_average_weight = 1
    elif product.order_unit not in [
        PRODUCT_ORDER_UNIT_PC_KG,
        PRODUCT_ORDER_UNIT_PC_PRICE_KG,
        PRODUCT_ORDER_UNIT_PC_PRICE_LT,
        PRODUCT_ORDER_UNIT_PC_PRICE_PC,
    ]:
        product.order_average_weight = DECIMAL_ZERO
    if product.order_unit in [
        PRODUCT_ORDER_UNIT_DEPOSIT,
        PRODUCT_ORDER_UNIT_MEMBERSHIP_FEE,
    ]:
        # No VAT on those products
        product.vat_level = VAT_100
    if product.order_unit not in [
        PRODUCT_ORDER_UNIT_PC_KG,
        PRODUCT_ORDER_UNIT_KG,
        PRODUCT_ORDER_UNIT_LT,
    ]:
        product.wrapped = False
    product.recalculate_prices(
        producer.producer_price_are_wo_vat,
        producer.price_list_multiplier,
    )

    if settings.REPANIER_SETTINGS_STOCK:
        if producer.represent_this_buyinggroup:
            product.producer_order_by_quantity = DECIMAL_ZERO
            product.limit_order_quantity_to_stock = True
            # IMPORTANT : Deactivate offeritem whose stock is not > 0 and product is into offer
            product.is_into_offer = (
                False if product.stock <= DECIMAL_ZERO else product.is_into_offer
            )
        if product.is_box:
            product.limit_order_quantity_to_stock = True
    else:
        product.limit_order_quantity_to_stock = False

    if not product.is_active:
        product.is_into_offer = False

    if product.customer_increment_order_quantity <= DECIMAL_ZERO:
        product.customer_increment_order_quantity = DECIMAL_ONE
    if product.customer_minimum_order_quantity <= DECIMAL_ZERO:
        product.customer_minimum_order_quantity = (
            product.customer_increment_order_quantity
        )
    if product.order_average_weight <= DECIMAL_ZERO:
        product.order_average_weight = DECIMAL_ONE
    if settings.REPANIER_SETTINGS_IS_MINIMALIST:
        if product.order_unit not in [
            PRODUCT_ORDER_UNIT_PC_KG,
            PRODUCT_ORDER_UNIT_KG,
            PRODUCT_ORDER_UNIT_LT,
        ]:
            if product.order_unit == PRODUCT_ORDER_UNIT_PC:
                product.customer_minimum_order_quantity = DECIMAL_ONE
            product.customer_alert_order_quantity = (
                product.customer_minimum_order_quantity * LIMIT_ORDER_QTY_ITEM
            ).quantize(THREE_DECIMALS)
        else:
            product.customer_alert_order_quantity = (
                product.customer_minimum_order_quantity
                + (
                    product.customer_increment_order_quantity
                    * (LIMIT_ORDER_QTY_ITEM - 1)
                )
            ).quantize(THREE_DECIMALS)
    if product.limit_order_quantity_to_stock:
        product.customer_alert_order_quantity = min(999, product.stock)
    if not product.reference:
        product.reference = uuid.uuid1()
    # Update stock of boxes containing this product
    # for box_content in product.box_content.all():
    #     if box_content.box is not None:
    #         box_content.box.save_update_stock()


@receiver(post_save, sender=Product)
def product_post_save(sender, **kwargs):
    product = kwargs["instance"]
    from repanier.models.box import BoxContent

    BoxContent.objects.filter(product_id=product.id).update(
        calculated_customer_content_price=F("content_quantity")
        * product.customer_unit_price.amount,
        calculated_content_deposit=F("content_quantity") * product.unit_deposit.amount,
    )
