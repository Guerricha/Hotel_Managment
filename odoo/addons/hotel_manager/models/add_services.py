from odoo import models, fields, _, api
import logging
_logger = logging.getLogger(__name__)

class HotelServices(models.Model):
    _name = 'hotel.services'
    _description = 'Hotel Model'
    _rec_name = 'service_id'

    service_id = fields.Char(string='Service Name', required=True)
    color = fields.Char(string='Color Index')  
    price = fields.Monetary(string='Price', currency_field='currency_id')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    property_account_income_id = fields.Many2one('account.account', string="Income Account")
    currency_id = fields.Many2one(
        'res.currency', 
        string='Currency', 
        required=True, 
        default=lambda self: self.env.company.currency_id
    )