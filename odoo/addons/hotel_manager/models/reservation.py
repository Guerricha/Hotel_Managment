from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class HotelReservation(models.Model):
    _name = 'hotel.reservation'
    _description = 'Hotel Reservation'
    _rec_name = 'reserv_id'

    #----------------HOTEL RESRVATION FIELDS-----------------------------------
    reserv_id = fields.Char(string='Reservation ID', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New')) 
    service_ids = fields.Many2many(
        'hotel.services', 'hotel_reservation_service_rel', 
        'reserv_id', 'service_id', string='Services'
    )
    guest_id = fields.Many2one('hotel.guest', string='Guest Name', required=True)
    first_name = fields.Char(string='First Name',related='guest_id.first_name')
    last_name = fields.Char(string='Last Name',related='guest_id.last_name')
    email = fields.Char(string='Email',related='guest_id.email')
    number = fields.Char(string='Phone Number',related='guest_id.number')
    age = fields.Integer(string='Age',related='guest_id.age', required=True)
    nin = fields.Char(string="NIN",related='guest_id.nin')  
    country_state = fields.Many2one("res.country.state", string="State",related='guest_id.country_state')
    country = fields.Many2one('res.country', string="Country", ondelete='restrict',related='guest_id.country')
    #reservation information
    check_in_date = fields.Date(string='Check-in Date', required=True)
    check_out_date = fields.Date(string='Check-out Date', required=True)
    room_id = fields.Many2one('hotel.room', string='Room', required=True)
    guest_line_ids = fields.One2many('hotel.reservation.guest.line', 'reserv_id', string='Guest Lines')
    service_line_ids = fields.One2many('hotel.reservation.service.line', 'reserv_id', string='Service Lines')
    services_total_price = fields.Monetary(string='Services Total Price', currency_field='currency_id', compute='_compute_services_total_price')
    total_price = fields.Monetary(string='Total Price', currency_field='currency_id', compute='_compute_total_price')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    nights = fields.Integer(string='Nights', compute='_compute_nights', store=True, default=0)
    num_adults = fields.Integer(string='Number of Adults', compute='_compute_num_adults')
    num_kids = fields.Integer(string='Number of Kids', compute='_compute_num_kids')
    nps_score = fields.Integer(string='NPS Score', default=-1)
    feedback = fields.Text(string='Feedback') 
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='draft')
    
    #----------------HOTEL RESRVATION COMPUTED FUNCTIONS-----------------------------------
    def button_confirm(self):self.write({'state': "confirm"})
    def button_draft(self):self.write({'state': "draft"})
    def button_cancel(self):self.write({'state': "cancel"})
    def button_done(self):
        self.write({'state': "done"})
        self.create_invoice()
        action = {
            'name': 'Net Promoter Score',
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.reservation.nps',
            'view_mode': 'form',
            'view_id': self.env.ref('hotel_manager.view_reservation_nps_form').id,
            'target': 'new',
            'context': {'default_reserv_id': self.id},
        }
        return action

    def create_invoice(self):
        if self.invoice_id:
            raise ValidationError(_("This reservation already has an invoice."))
        invoice_lines = []

        # Add room charges
        if self.room_id:
            room = self.room_id
            if not room.product_id:
                raise ValidationError(_("The room %s does not have a linked product.") % room.room_id)
            account_id = room.property_account_income_id.id
            if not account_id:
                raise ValidationError(_("Please define an income account for the room: %s") % room.room_id)

            invoice_lines.append((0, 0, {
                'product_id': room.product_id.id,
                'quantity': self.nights, 
                'price_unit': room.price, 
                'account_id': account_id,
            }))

        # Add service charges
        for line in self.service_line_ids:
            service = line.service_id
            if not service.product_id:
                raise ValidationError(_("The service %s does not have a linked product.") % service.service_id)

            account_id = service.property_account_income_id.id
            if not account_id:
                raise ValidationError(_("Please define an income account for the service: %s") % service.service_id)

            invoice_lines.append((0, 0, {
                'quantity': line.quantity,
                'price_unit': line.price_unit,
                'account_id': account_id,
            }))

        # Create the invoice
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines,
        })

        self.invoice_id = invoice.id

    @api.depends('guest_line_ids.guest_id')
    def _compute_num_adults(self):
        for reservation in self:
            num_adults = len([guest.guest_id.age for guest in reservation.guest_line_ids if guest.guest_id.age >= 18])
            reservation.num_adults = num_adults

    @api.depends('guest_line_ids.guest_id')
    def _compute_num_kids(self):
        for reservation in self:
            num_kids = len([guest.guest_id.age for guest in reservation.guest_line_ids if guest.guest_id.age < 18])
            reservation.num_kids = num_kids

    @api.depends('check_in_date', 'check_out_date')
    def _compute_nights(self):
        for reservation in self:
            if reservation.check_in_date and reservation.check_out_date:
                nights = (reservation.check_out_date - reservation.check_in_date).days
                reservation.nights = nights

    @api.onchange('country')
    def _onchange_country_id(self):
        if self.country and self.country_state and self.country_state.country_id != self.country:
            self.country_state = False

    @api.onchange('guest_id')
    def _check_age(self):
        if self.guest_id.age and self.guest_id.age < 18 :
            raise ValidationError(_("You must be older then 18 in order to reserve."))

    @api.depends('services_total_price', 'room_id', 'check_in_date', 'check_out_date', 'nights')
    def _compute_total_price(self):
        for reservation in self:
            if reservation.check_in_date and reservation.check_out_date and reservation.room_id.price and reservation.services_total_price and reservation.nights:
                reservation.total_price = reservation.room_id.price * reservation.nights + reservation.services_total_price
            elif reservation.check_in_date and reservation.check_out_date and reservation.room_id.price and reservation.nights:
                reservation.total_price = reservation.room_id.price * reservation.nights 
            else:
                reservation.total_price = 0

    @api.depends('service_line_ids.total_price')
    def _compute_services_total_price(self):
        for reservation in self:
            if reservation.service_line_ids:
                reservation.services_total_price = sum(reservation.service_line_ids.mapped('total_price'))
            else:
                reservation.services_total_price = 0

    @api.onchange('check_in_date', 'check_out_date')
    def _check_dates(self):
        if self.check_in_date and self.check_out_date and self.check_out_date <= self.check_in_date:
            raise ValidationError(_("Check-out date must be higher than check-in date."))
        if self.check_in_date and self.check_in_date < fields.Date.today():
            raise ValidationError(_("Check-in date must be today or later."))

    @api.onchange('room_id')
    def _check_room_availability(self):
        if self.room_id and self.room_id.state == 'under_maintenance':
            raise ValidationError(_("Selected room is unavailable due to maintenance."))
        if self.room_id and self.room_id.state == 'reserved':
            raise ValidationError(_("Selected room is already reserved."))
        else:
            self.room_id.state = 'reserved'

    @api.model
    def make_rooms_available(self):
        reservations = self.search([])
        for reservation in reservations:
            if (reservation.check_out_date < fields.Date.today() or not reservation.exists()) and reservation.room_id.state == 'reserved':
                reservation.room_id.state = 'available'
            elif reservation.check_out_date >= fields.Date.today() and reservation.room_id.state == 'available':
                reservation.room_id.state = 'reserved'
            elif reservation.room_id.state == 'under_maintenance':
                reservation.room_id.state = 'under_maintenance'
    
    @api.model
    def write(self, vals):
        res = super(HotelReservation, self).write(vals)
        for record in self:
            record._create_services_lines()
        return res

    @api.model
    def create(self, vals):
        if vals.get('reserv_id', _('New')) == _('New'):
            vals['reserv_id'] = self.env['ir.sequence'].next_by_code('reservation.sequence') or _('New')
        reservation = super(HotelReservation, self).create(vals)
        reservation._create_guest_line()
        reservation._create_services_lines()
        return reservation

    
    def _create_guest_line(self):
        self.env['hotel.reservation.guest.line'].create({
            'reserv_id': self.id,  
            'guest_id': self.guest_id.id, 
        })

    def _create_services_lines(self):
        for service in self.service_ids:
            if not self.service_line_ids.filtered(lambda line: line.service_id == service):
                self.env['hotel.reservation.service.line'].create({
                    'reserv_id': self.id,   
                    'service_id': service.id, 
                    'quantity' : 1,
                    'price_unit' : service.price, 
                })


#----------------HOTEL RESRVATION NPS CLASS-----------------------------------
class HotelReservationNPS(models.TransientModel):
    _name = 'hotel.reservation.nps'
    _description = 'Reservation NPS score'

    nps_score = fields.Integer(string='NPS Score', default=0)
    feedback = fields.Text(string='Feedback') 

    @api.constrains('nps_score')
    def _check_nps_score(self):
        for record in self:
            if record.nps_score < 0 or record.nps_score > 10:
                raise ValidationError("NPS Score must be between 0 and 10.")
            
    def action_confirm(self):
        reservation_id = self.env.context.get('active_id')
        reservation = self.env['hotel.reservation'].browse(reservation_id)
        if reservation:
            reservation.write({
                'nps_score': self.nps_score,
                'feedback': self.feedback,
            })
        return {'type': 'ir.actions.act_window_close'}


#----------------HOTEL RESRVATION SERVICES LINES CLASS-----------------------------------
class HotelReservationServiceLine(models.Model):
    _name = 'hotel.reservation.service.line'
    _description = 'Reservation Service Line'

    reserv_id = fields.Many2one('hotel.reservation', string='Reservation', ondelete='cascade')
    service_id = fields.Many2one('hotel.services', string='Service', required=True)
    quantity = fields.Integer(string='Quantity', default=1)
    price_unit = fields.Monetary(string='Unit Price', related='service_id.price')
    total_price = fields.Monetary(string='Total', compute='_compute_total_price', store=True)
    currency_id = fields.Many2one(related='reserv_id.currency_id', string='Currency', store=True)

    @api.depends('quantity', 'price_unit')
    def _compute_total_price(self):
        for line in self:
            line.total_price = line.quantity * line.price_unit


#----------------HOTEL RESRVATION GUESTS LINES CLASS-----------------------------------
class HotelReservationGuestLine(models.Model):
    _name = 'hotel.reservation.guest.line'
    _description = 'Reservation Guests Line'

    reserv_id = fields.Many2one('hotel.reservation', string='Reservation', ondelete='cascade')
    guest_id = fields.Many2one('hotel.guest', string='Guest Name', required=True)    
    first_name = fields.Char(string='First Name',related='guest_id.first_name', required=True)
    last_name = fields.Char(string='Last Name',related='guest_id.last_name', required=True)
    email = fields.Char(string='Email',related='guest_id.email')
    number = fields.Char(string='Phone Number',related='guest_id.number')
    age = fields.Integer(string='Age',related='guest_id.age', required=True)
    nin = fields.Char(string="NIN",related='guest_id.nin')  
    country_state = fields.Many2one("res.country.state", string="State",related='guest_id.country_state')
    country = fields.Many2one('res.country', string="Country", ondelete='restrict',related='guest_id.country')
    