# Copyright <YEAR(S)> <AUTHOR(S)>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def send_to_gapp(self):
        pass
