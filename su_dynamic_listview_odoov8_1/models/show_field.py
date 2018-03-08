# -*- coding: utf-8 -*-
# © 2017 truongdung
# © 2018 Diagram Software S.L.

from ast import literal_eval
from collections import OrderedDict
import logging

from openerp import SUPERUSER_ID
from openerp import _, api, fields, models
from openerp.exceptions import ValidationError, Warning as UserError
from openerp.modules.registry import RegistryManager

from lxml import etree

_logger = logging.getLogger(__name__)


class ShowField(models.Model):
    _name = 'show.field'

    fields_show = fields.Char(string='Fields Show', default='[]')
    model = fields.Char(string='Model Name')
    view_id = fields.Many2one(string='View', comodel_name='ir.ui.view')
    for_all_user = fields.Boolean(string='Apply for All Users', default=False)

    @api.one
    @api.constrains('fields_show', 'model')
    def _check_fields_show(self):
        fields_show = literal_eval(self.fields_show)
        if not isinstance(fields_show, (list,)):
            raise ValidationError(
                _('Wrong definition format: %s') % (fields_show,))

        for elem in fields_show:
            tag = elem.get('tag')
            validator = getattr(self, '_validate_%s' % (tag,), self._validate_unknown)
            validator(elem)

    @api.model
    def _validate_unknown(self, elem):
        raise ValidationError(
            _('Unknown element: %s') % (elem,))

    @api.model
    def _validate_field(self, field):
        req_attrs = set(['tag', 'name', 'string', 'sequence'])
        if not req_attrs.issubset(field):
            raise ValidationError(
                _('Wrong field definition: %s') % (field,))
        if not field['name']:
            raise ValidationError(
                _('Field name not found: %s') % (field,))
        if not self.env['ir.model.fields'].search([
            ('model', '=', self.model),
            ('name', '=', field['name'])
        ], limit=1):
            raise ValidationError(
                _('Unknown field "%s"') % (field['name'],))

    @api.model
    def _validate_button(self, button):
        req_attrs = set(['tag', 'name', 'string', 'sequence', 'type', 'icon'])
        if not req_attrs.issubset(button):
            raise ValidationError(
                _('Wrong button definition: %s') % (button,))
        if not button['name']:
            raise ValidationError(
                _('Button name not found: %s') % (button,))
        try:
            if button['type'] == 'action':
                action = self.env.ref(button['name'])
                if not action.id:
                    raise ValidationError(
                        _('Unknown button "%s" action.') % (button['name'],))
            elif button['type'] == 'object':
                Model = self.env[self.model]
                if not hasattr(Model, button['name']):
                    raise ValidationError(
                        _('Unknown button "%s" method: %s.%s') % (self.mode, button['name']))
            else:
                raise ValidationError(
                    _('Unknown button "%s" tag: %s') % (button['name'], button['tag']))
        except ValueError as e:
            raise ValidationError(
                _('Unknown button "%s": %s') % (button['name'], e.message))

    @api.model
    def change_fields(self, values):
        records = self.search([
            ('model', '=', values.get('model', False)),
            ('create_uid', '=', self.env.user.id),
            ('view_id', '=', values.get('view_id', False))])

        fields_show = values.get('fields_show', [])

        def get_xmlid(id):
            IrActionsActWindow = self.env['ir.actions.act_window']
            try:
                id = int(id)
                xmlid = IrActionsActWindow.browse(id).get_external_id()[id]
                if not xmlid:
                    raise UserError(
                        _('No defined external ID for action %s.') % (id,))
                return xmlid
            except (ValueError, KeyError):
                raise UserError(
                    _('Unable to get external ID for action %s.') % (id,))

        # Convert button action's integer ID to external ID
        for elem in fields_show:
            if elem.get('tag') == 'button' and elem.get('type') == 'action':
                elem['name'] = get_xmlid(elem['name'])

        values['fields_show'] = repr(fields_show)
        if records:
            records[0].write(values)
        else:
            self.create(values)

        return True

    @api.model
    def reset_fields(self, values):
        return self.search([
            ('model', '=', values.get('model', False)),
            ('create_uid', '=', self.env.user.id),
            ('view_id', '=', values.get('view_id', False))
        ]).unlink()

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

                        # Get all fields/buttons and hide them
                        for _elem in doc.xpath('//*[self::field or self::button]'):
                            if 'name' in _elem.attrib:
                                field_base[_elem.attrib.get('name')] = _elem
                                _elem.set('invisible', '1')
                                doc.remove(_elem)

                        # Get existing fields/buttons or create new ones. Unhide them all
                        for _attrs in fields_show:
                            name = _attrs['name']
                            if _attrs.get('tag') == 'button' and _attrs.get('type') == 'action':
                                # Button action's external ID must be converted to integer ID
                                try:
                                    name = str(self.env.ref(_attrs['name']).id)
                                except ValueError:
                                    _logger.exception('Unknown action: %s', _attrs['name'])
                                    continue

                            _elem = field_base.pop(name, None)
                            if _elem is None:
                                _elem = etree.Element(_attrs.get('tag', 'field'))
                                _elem.set('name', name)
                                if _attrs.get('tag') == 'button':
                                    _elem.set('id', _elem.get('name'))
                                    _elem.set('type', _attrs['type'])
                                    _elem.set('icon', _attrs['icon'])

                            _elem.set('string', _attrs['string'])
                            _elem.set('invisible', '0')

                            doc.xpath('//tree')[0].append(_elem)

                        # Append remaining fields/buttons. They remain hidden.
                        for _elem in field_base.itervalues():
                            doc.xpath('//tree')[0].append(_elem)

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
