# __author__ = 'truongdung'
from openerp import fields, api, models
from openerp.models import BaseModel, AbstractModel
from lxml import etree
import logging
_logger = logging.getLogger(__name__)


class SUShowFields(models.Model):
    _name = "show.field"

    fields_show = fields.Char(string="Fields Show", default="[]")
    model = fields.Char(string="Model Name")
    view_id = fields.Many2one(string="View id", comodel_name="ir.ui.view")
    for_all_user = fields.Boolean(string="Apply for All Users", default=False)

    @api.model
    def change_fields(self, values):
        records = self.search([("model", "=", values.get("model", False)),
                               ("create_uid", "=", self.env.user.id),
                               ("view_id", '=', values.get("view_id", False))])
        values['fields_show'] = str(values.get('fields_show', {}))
        if records:
            records[0].write(values)
        else:
            self.create(values)
        return True

SUShowFields()

_fields_view_get = BaseModel.fields_view_get


@api.model
def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    res = _fields_view_get(self, view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    hide_button = True
    if view_type in ['list', 'tree'] and 'show.field' in self.env.registry.models:
        shf_obj = self.env['show.field'].search([('model', '=', self._name),
                                                 ('view_id', '=', res.get('view_id', False)),
                                                 ('create_uid', '=', 1)], limit=1)
        if not shf_obj.for_all_user:
            hide_button = False
            shf_obj = self.env['show.field'].search([('model', '=', self._name),
                                                     ('view_id', '=', res.get('view_id', False)),
                                                     ('create_uid', '=', self.env.user.id)], limit=1)
        res['for_all_user'] = shf_obj.for_all_user
        if shf_obj:
            doc = etree.XML(res['arch'])
            fields_show = eval(shf_obj[0].fields_show)
            field_base = {}
            for x in doc.xpath("//field"):
                if 'name' in x.attrib:
                    field_base[x.attrib.get('name')] = x
                    x.set("invisible", "1")
                    doc.remove(x)
            for _field_name in fields_show:
                if _field_name['name'] in field_base:
                    _field = field_base[_field_name['name']]
                    _field.set("invisible", "0")
                    _field.set("string", _field_name['string'])
                    field_base.pop(_field_name['name'])
                else:
                    _field = etree.Element(
                        'field', {'name': _field_name['name'], 'string': _field_name['string']})
                doc.xpath("//tree")[0].append(_field)
            for _field_name in field_base:
                doc.xpath("//tree")[0].append(field_base[_field_name])
            res['arch'] = etree.tostring(doc)
            _arch, _fields = self.env['ir.ui.view'].postprocess_and_fields(
                self._name, etree.fromstring(res['arch']), view_id)
            res['arch'] = _arch
            res['fields'] = _fields
    res['fields_get'] = self.env[self._name].fields_get()
    res['hide_button'] = hide_button
    return res

BaseModel.fields_view_get = fields_view_get
