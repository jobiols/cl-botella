# Copyright 2019 jeo Software
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from datetime import date
from odoo import models, api, exceptions, _


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

        datas = self.encode_data_file()

        attachment = self.env['ir.attachment'].create({
            'name': self.data_filename(),
            'datas': base64.b64encode(datas),
            'datas_fname': 'GAPP.txt',
            'res_model': 'stock.picking',
            'res_id': self.id,
        })

        template_id.attachment_ids = [(4, attachment.id)]
        gapp = self.env['res.partner'].search([('ref', '=', 'gapp')])

        # enviar el mail con el attach
        template_id.send_mail(gapp.id, raise_exception=False, force_send=True)

    def data_filename(self):
        """ Genera el nombre para el archivo GAPP
            NNNNNNNNN_DDMMYYYY
        """
        today = date.today()
        return '{:09}_{}.TXT'.format(self.id, today.strftime('%d%m%Y'))

    def encode_state(self, state_id):
        return 'BUE'

    def encode_data_file(self):
        """ Codificar archivo para GAPP
        """
        datas = b''
        for line in self.move_lines:
            cols = list()

            # 1. Código del propietario del LOTE/ARCHIVO.
            cols.append('RANDOM')

            # 2. Letra del comprobante que respalda el pedido. Ej:”A”
            origin = self.origin
            sale_order_obj = self.env['sale.order']
            so = sale_order_obj.search([('name', '=', origin)])
            if not so:
                raise exceptions.UserError(_('No se puede encontrar la orden '
                                             'de venta relacionada con este '
                                             'envio.'))
            if not so.invoice_ids[0]:
                raise exceptions.UserError(_('No se puede encontrar la '
                                             'factura de venta que respalda '
                                             'este envio.'))
            letter = so.invoice_ids[0].document_letter_name
            cols.append('{}'.format(letter))

            # 3. Centro Emisor (Uso Interno) Siempre = “001”
            cols.append('001')

            # 4. Numero de pedido. El numero que representa al pedido registro.
            cols.append('{:010}'.format(self.id))

            # 5. Código del cliente/sucursal a la que pertenece el pedido.
            ref = self.partner_id.ref
            try:
                ref = int(ref)
            except:
                raise exceptions.UserError(_('La referencia del cliente debe '
                                             'ser un numero'))
            cols.append('{:010}'.format(ref))

            # 6. Es la fecha propuesta de entrega al cliente.
            dt = self.scheduled_date
            if dt:
                cols.append('{}'.format(dt.strftime('%d/%m/%Y')))
            else:
                cols.append('')

            # 7. Nombre o razón social asociado al campo 5, que representa al
            # destinatario del pedido.
            name = self.partner_id.name
            cols.append('{}'.format(name))

            # 8. Código postal asociado a la dirección del destinatario.
            zipcode = self.partner_id.zip
            if zip:
                cols.append('{}'.format(zipcode))
            else:
                cols.append('')

            # 9. Nombre de la calle y altura asociado a la dirección del
            # destinatario.
            street = self.partner_id.street
            cols.append('{}'.format(street))

            # 10. Nombre de la localidad asociada a la dirección del
            # destinatario.
            city = self.partner_id.street2 or ''
            city += ' ' + self.partner_id.state_id.name or ''
            cols.append('{}'.format(city))

            # 11. Código de provincia asociada a la dirección del destinatario.
            provincia = self.encode_state(self.partner_id.state_id.code or '')
            if provincia:
                cols.append('{}'.format(provincia))
            else:
                cols.append('')

            # 12. Peso asociado a la cantidad de productos de la línea actual
            # del archivo. Ej: Si se solicitan 10 unidades  del producto
            # 000001, que el peso individual es 2.5 kilos, el valor
            # será = 25.000 (veinticinco con 3 ceros decimales).
            peso = self.weight
            if peso:
                cols.append('{0:0.3f}'.format(peso))
            else:
                cols.append('')

            # 13. Una observación asociada al pedido.
            obs = self.note
            cols.append('{}'.format(obs))

            # 14. Código del producto solicitado.
            default_code = line.product_id.default_code
            cols.append('{}'.format(default_code))

            # 15. Cantidad solicitada del producto en el registro vigente.
            qty = line.product_qty
            cols.append('{:010.3f}'.format(qty))

            # 16. Lote particular al cual debe pertenecer el producto
            # solicitado.
            lot = ''
            cols.append('{}'.format(lot))

            # 17. Código seriado del producto solicitado.
            serial = ''
            cols.append('{}'.format(serial))

            # 18. Monto, Subtotal o importe que representa la cantidad
            # solicitada del producto en el registro. (Sin incluir IVA).
            monto = ''
            cols.append('{}'.format(monto))

            line_data = ';'.join(cols)

            datas += b'%s\r\n' % bytes(line_data, encoding='utf8')

        return datas
