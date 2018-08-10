# -*- coding: utf-8
from django import forms
from django.conf import settings
from django.contrib import admin
from django.utils import translation
from django.utils.translation import ugettext_lazy as _, get_language_info
from parler.admin import TranslatableAdmin
from parler.forms import TranslatableModelForm

from repanier.admin.admin_filter import ContractFilterByProducer
from repanier.models import Contract
from repanier.models import Customer
from repanier.models import Producer


class ContractDataForm(TranslatableModelForm):
    producers = forms.ModelMultipleChoiceField(
        Producer.objects.filter(is_active=True),
        label=_('Producers'),
        widget=admin.widgets.FilteredSelectMultiple(_('Producers'), False),
        required=True
    )

    def clean(self):
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return

        if self.instance.id is None:
            if self.language_code != settings.LANGUAGE_CODE:
                # Important to also prohibit untranslated instance in settings.LANGUAGE_CODE
                self.add_error(
                    'long_name',
                    _('Please define first a long_name in %(language)s') % {
                        'language': get_language_info(settings.LANGUAGE_CODE)['name_local']})


class ContractAdmin(TranslatableAdmin):
    form = ContractDataForm
    model = Contract

    list_display = ('get_contract_admin_display',)
    list_display_links = ('get_contract_admin_display',)
    list_filter = [
        'is_active',
        ContractFilterByProducer
    ]
    date_hierarchy = 'first_permanence_date'
    list_per_page = 16
    list_max_show_all = 16
    ordering = (
        'first_permanence_date',
    )
    search_fields = ('translations__long_name',)

    def has_delete_permission(self, request, contract=None):
        user = request.user
        if user.is_order_manager or user.is_invoice_manager:
            return settings.REPANIER_SETTINGS_CONTRACT
        return False

    def has_add_permission(self, request):
        return self.has_delete_permission(request)

    def has_change_permission(self, request, contract=None):
        return self.has_delete_permission(request, contract)

    def get_list_display(self, request):
        list_display = [
            'get_contract_admin_display', 'get_producers'
        ]
        if settings.DJANGO_SETTINGS_MULTIPLE_LANGUAGE:
            list_display += [
                'language_column',
            ]
        return list_display

    def get_fieldsets(self, request, contract=None):
        fields_basic = [
            ('long_name', 'picture2'),
            'first_permanence_date',
            'recurrences'
        ]
        if contract is not None:
            fields_basic += [
                'get_dates'
            ]
        fields_basic += [
            'producers',
            'customers',
            'is_active'
        ]
        fieldsets = (
            (None, {'fields': fields_basic}),
        )
        return fieldsets

    def get_readonly_fields(self, request, contract=None):
        if contract is not None:
            return ['get_dates', 'customers']
        else:
            return ['customers']

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "customers":
            kwargs["queryset"] = Customer.objects.filter(may_order=True, represent_this_buyinggroup=False)

    def get_queryset(self, request):
        qs = super(ContractAdmin, self).get_queryset(request)
        qs = qs.filter(
            # Important to also display untranslated contracts : translations__language_code=settings.LANGUAGE_CODE
            translations__language_code=settings.LANGUAGE_CODE
        )
        return qs
