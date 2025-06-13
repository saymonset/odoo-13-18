# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class Profit_margin(models.Model):
    _name = 'profit_margin'
    _description = 'Profit_margin'

    name = fields.Char('Name')
    pricelist_id = fields.Many2one('product.pricelist', string='Price List')
    
    @api.onchange('pricelist_id')
    def _onchange_pricelist_id(self):
        if self.pricelist_id:
            # Imprimir el ID y el nombre de la lista de precios en el backend
            _logger.info("Selected Price List ID: %s", self.pricelist_id.id)
            _logger.info("Selected Price List Name: %s", self.pricelist_id.name)
