# Copyright 2019 jeo Software
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp import models
import base64


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def send_to_gapp(self):
        """ Enviar el archivo attachado a GAPP
        """

        template_id = self.env.ref(
            'gapp_logistic_connector.gapp_mail_template')

        # have model_description in template language
        lang = self.env.context.get('lang')
        if template_id and template_id.lang:
            lang = template_id._render_template(template_id.lang,
                                                'stock.picking', self.id)
        self = self.with_context(lang=lang)

        datas = b''
        for line in self.move_lines:
            datas += b'%s;bbb;ccc\r\n' % bytes(line.name, encoding='utf8')

        attachment = self.env['ir.attachment'].create({
            'name': 'GAPP.txt',
            'datas': base64.b64encode(datas),
            'datas_fname': 'GAPP.txt',
            'res_model': 'stock.picking',
            'res_id': self.id,
        })
        self.write({'attachment_id': attachment.id})

        # enviar el mail con el attach
        template_id.send_mail()

    def make_file(self, lines):
        f = tempfile.NamedTemporaryFile()
        f.name = 'mi_nombre'
        for line in lines:
            f.write('%s;bbb;ccc\r\n' % line.name)
