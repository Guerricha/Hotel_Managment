from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

class HotelRoom(models.Model):
    _name = 'hotel.room'
    _description = 'Hotel Room'
    _rec_name = 'room_id'

    room_id = fields.Char(string='Room number', required=True, copy=False, readonly=True
                          , index=True, default=lambda self: _('New'))
    single_bed = fields.Integer(string='Singel bed')
    double_bed = fields.Integer(string='Double bed')
    price = fields.Monetary(string='Price per Night', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    description = fields.Text(string='Description')
    state = fields.Selection([
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('under_maintenance', 'Under Maintenance'),
    ], default='available')
    capacity = fields.Integer(string='Capacity', compute='_compute_capacity', store=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    property_account_income_id = fields.Many2one('account.account', string="Income Account")
    reserv_ids = fields.One2many('hotel.reservation', 'room_id', string='Reservations'
                                 , readonly=True)

    def button_free(self):self.write({'state': "available"})
    def button_reserve(self):self.write({'state': "reserved"})
    def button_maintenance(self):self.write({'state': "under_maintenance"})

    @api.depends('single_bed', 'double_bed')
    def _compute_capacity(self):
        for room in self:
            room.capacity = room.single_bed + 2*room.double_bed
    
    @api.model
    def create(self, vals):
        if vals.get('room_id', _('New')) == _('New'):
            vals['room_id'] = self.env['ir.sequence'].next_by_code('room.sequence') or _('New')
        return super(HotelRoom, self).create(vals)
   