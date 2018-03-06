# -*- coding: utf-8 -*-
# © 2017 truongdung
# © 2018 Diagram Software S.L.

from ast import literal_eval
from collections import OrderedDict
import logging

from openerp import SUPERUSER_ID
from openerp import _, api, fields, models
from openerp.exceptions import ValidationError
from openerp.modules.registry import RegistryManager

from lxml import etree

_logger = logging.getLogger(__name__)


class ShowField(models.Model):
    _name = 'show.field'

    fields_show = fields.Char(string='Fields Show', default='[]')
    model = fields.Char(string='Model Name')
    view_id = fields.Many2one(string='View id', comodel_name='ir.ui.view')
    for_all_user = fields.Boolean(string='Apply for All Users', default=False)

    @api.one
    @api.constrains('fields_show', 'model')
    def _check_fields_show(self):
        IrModelFields = self.env['ir.model.fields']

        fields_show = literal_eval(self.fields_show)
        if not isinstance(fields_show, (list,)):
            raise ValidationError(
                _('__MSG__WRONG_FORMAT: %s') % (fields_show,))

        req_attrs = set(['name', 'string', 'sequence'])
        for field in fields_show:
            if not req_attrs.issubset(field):
                raise ValidationError(
                    _('__MSG__WRONG_FIELD_DEFINITION: %s') % (field,))
            if not field['name']:
                raise ValidationError(
                    _('__MSG__NO_FIELD_NAME: %s') % (field,))
            if not IrModelFields.search([
                ('model', '=', self.model),
                ('name', '=', field['name'])
            ], limit=1):
                raise ValidationError(
                    _('__MSG__UNKNOWN_FIELD: %s') % (field['name'],))

    @api.model
    def change_fields(self, values):
        records = self.search([
            ('model', '=', values.get('model', False)),
            ('create_uid', '=', self.env.user.id),
            ('view_id', '=', values.get('view_id', False))])

        fields_show = values.get('fields_show', [])
        values['fields_show'] = repr(fields_show)

        if records:
            records[0].write(values)
        else:
            self.create(values)

        return True

    @api.cr
    def _register_hook(self, cr, ids=None):
        """
        Wrap the method `fields_view_get` of the models specified by the
        rules given by `ids` (or all existing rules if `ids` is `None`.)
        """
        def wrap_fields_view_get():
            @api.model
            def fields_view_get(
                    self, view_id=None, view_type='form', toolbar=False,
                    submenu=False):
                res = fields_view_get.origin(
                    self, view_id=view_id, view_type=view_type,
                    toolbar=toolbar, submenu=submenu)

                ShowField = self.env['show.field']
                IrUiView = self.env['ir.ui.view']
                hide_button = True

                if view_type in ['list', 'tree']:
                    shf_obj = ShowField.search([
                        ('model', '=', self._name),
                        ('view_id', '=', res.get('view_id', False)),
                        ('create_uid', '=', 1)], limit=1)

                    if not shf_obj.for_all_user:
                        hide_button = False
                        shf_obj = ShowField.search([
                            ('model', '=', self._name),
                            ('view_id', '=', res.get('view_id', False)),
                            ('create_uid', '=', self.env.user.id)], limit=1)

                    res['for_all_user'] = shf_obj.for_all_user

                    if shf_obj:
                        doc = etree.XML(res['arch'])
                        fields_show = literal_eval(shf_obj.fields_show or '[]')
                        field_base = OrderedDict()

                        for _field in doc.xpath('//field'):
                            if 'name' in _field.attrib:
                                field_base[_field.attrib.get('name')] = _field
                                _field.set('invisible', '1')
                                doc.remove(_field)

                        for _field_name in fields_show:
                            _field = field_base.pop(_field_name['name'], None)
                            if _field is None:
                                _field = etree.Element('field')
                            _field.set('invisible', '0')
                            _field.set('name', _field_name['name'])
                            _field.set('string', _field_name['string'])
                            doc.xpath('//tree')[0].append(_field)

                        for _field in field_base.itervalues():
                            doc.xpath('//tree')[0].append(_field)

                        res['arch'] = etree.tostring(doc)
                        _arch, _fields = IrUiView.postprocess_and_fields(
                            self._name, etree.fromstring(res['arch']), view_id)
                        res['arch'] = _arch
                        res['fields'] = _fields

                res['fields_get'] = self.fields_get()
                res['hide_button'] = hide_button

                return res

            return fields_view_get

        updated = False

        if ids is None:
            ids = self.search(cr, SUPERUSER_ID, [])

        for shf in self.browse(cr, SUPERUSER_ID, ids):
            model = shf.model
            model_obj = self.pool.get(model)

            if model_obj and not hasattr(model_obj, '_show_field_enabled'):
                # monkey-patch method `fields_view_get`
                _logger.debug('Monkey-patching %s.fields_view_get...', model)
                model_obj._patch_method(
                    'fields_view_get', wrap_fields_view_get())
                setattr(model_obj, '_show_field_enabled', True)
                updated = True

        return updated

    @api.model
    def create(self, vals):
        res = super(ShowField, self).create(vals)
        if self._register_hook(res.ids):
            RegistryManager.signal_registry_change(self.env.cr.dbname)
        return res

    @api.multi
    def write(self, vals):
        res = super(ShowField, self).write(vals)
        if self._register_hook(self.ids):
            RegistryManager.signal_registry_change(self.env.cr.dbname)
        return res
