from odoo import models, fields, api
from datetime import timedelta
from dateutil.relativedelta import relativedelta

class HotelAnalysis(models.Model):
    _name = 'hotel.analysis'
    _description = 'Hotel Analysis'

    # Date of the analysis record
    date = fields.Date(string='Date', required=True)
    
    # Total revenue from room bookings, computed based on related reservations
    total_room_revenue = fields.Monetary(string='Total Room Revenue', compute='_compute_totals', currency_field='currency_id', store=True)
    
    # Percentage of repeated guests
    repeated_guest_percentage = fields.Float(string='Repeated Guest Percentage (%)', compute='_compute_rgp', default=0, store=True)
    
    # Total number of available rooms on the given date
    total_available_rooms = fields.Integer(string='Total Available Rooms', compute='_compute_totals', store=True)
    
    # Revenue per available room (RevPAR)
    revpar = fields.Monetary(string='RevPAR', compute='_compute_revpar', currency_field='currency_id', store=True)
    
    # Average Daily Rate (ADR)
    adr = fields.Monetary(string='ADR', compute='_compute_adr', currency_field='currency_id', store=True)
    
    # Occupancy rate percentage
    occupancy_rate = fields.Float(string='Occupancy Rate (%)', compute='_compute_occupancy_rate', store=True)
    
    # Total revenue from other services
    total_other_revenue = fields.Monetary(string='Total Other Revenue', compute='_compute_totals', currency_field='currency_id', store=True)
    
    # Total Revenue Per Available Room (TRevPAR)
    trevpar = fields.Monetary(string='TRevPAR', compute='_compute_trevpar', currency_field='currency_id', store=True)
    
    # Number of loyal guests
    loyal_guests = fields.Integer(string='Loyal Guests', default=0, compute='_compute_loyal_guests', store=True)
    
    # Currency used for monetary values, defaulting to the company's currency
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    @api.depends('date')
    def _compute_rgp(self):
        """Compute the percentage of repeated guests."""
        for record in self:
            reservations = self.env['hotel.reservation'].search([
                ('check_in_date', '>=', record.oldest_check_in_date()),
                ('check_out_date', '<=', record.date),
            ])
            total_reservations = len(reservations)
            repeated_guests = len(set(reservations.mapped('guest_id')))
            if total_reservations > 0:
                record.repeated_guest_percentage = (repeated_guests / total_reservations) * 100
            else:
                record.repeated_guest_percentage = 0

    @api.depends('total_room_revenue', 'total_available_rooms', 'total_other_revenue')
    def _compute_trevpar(self):
        """Compute Total Revenue Per Available Room (TRevPAR)."""
        for record in self:
            total_revenue = record.total_room_revenue + record.total_other_revenue
            if record.total_available_rooms > 0:
                record.trevpar = total_revenue / record.total_available_rooms
            else:
                record.trevpar = 0

    @api.depends('date')
    def _compute_totals(self):
        """Compute total revenue, total available rooms, and total other revenue."""
        for record in self:
            reservations = self.env['hotel.reservation'].search([
                ('check_in_date', '>=', record.oldest_check_in_date()),
                ('check_out_date', '<=', record.date),
                ('state', 'not in', ('draft', 'cancel')),
            ])
            record.total_room_revenue = sum(reservations.mapped('total_price'))
            record.total_other_revenue = sum(reservations.mapped('services_total_price'))
            record.total_available_rooms = self.env['hotel.room'].search_count([('state', 'in', ('available')), ])

    @api.depends('total_room_revenue', 'total_available_rooms')
    def _compute_revpar(self):
        """Compute Revenue per Available Room (RevPAR)."""
        for record in self:
            if record.total_available_rooms > 0:
                record.revpar = record.total_room_revenue / record.total_available_rooms
            else:
                record.revpar = 0

    @api.depends('total_room_revenue', 'total_available_rooms')
    def _compute_adr(self):
        """Compute Average Daily Rate (ADR)."""
        for record in self:
            occupied_rooms = self.env['hotel.reservation'].search_count([
                ('check_in_date', '>=', record.oldest_check_in_date()),
                ('check_out_date', '<=', record.date),
                ('state', 'not in', ('draft', 'cancel')), 
            ])
            if occupied_rooms > 0:
                record.adr = record.total_room_revenue / occupied_rooms
            else:
                record.adr = 0

    @api.depends('date')
    def _compute_loyal_guests(self):
        """Compute the number of loyal guests."""
        self.loyal_guests = self.env['hotel.guest'].search_count([('loyalty_status', '=', True)])

    @api.depends('total_available_rooms')
    def _compute_occupancy_rate(self):
        """Compute the occupancy rate percentage."""
        for record in self:
            occupied_rooms = self.env['hotel.room'].search_count([
                ('state', 'in', ('reserved')), 
            ])
            if record.total_available_rooms > 0:
                record.occupancy_rate = (occupied_rooms / record.total_available_rooms) * 100
            else:
                record.occupancy_rate = 0

    def oldest_check_in_date(self):
        """Retrieve the oldest check-in date from reservations."""
        oldest_reservation = self.env['hotel.reservation'].search([], order='check_in_date asc', limit=1)
        if oldest_reservation:
            return oldest_reservation.check_in_date
        return fields.Date.today()

    @api.model
    def update_analysis_data(self):
        """Update analysis data for each day between the oldest and newest reservations."""
        reservations = self.env['hotel.reservation'].search([], order='check_in_date asc')
        if not reservations:
            return

        oldest_date = reservations[0].check_in_date
        newest_date = reservations[-1].check_out_date

        current_date = oldest_date

        while current_date <= newest_date:
            existing_record = self.search([('date', '=', current_date)], limit=1)
            
            if not existing_record:
                new_record = self.create({
                    'date': current_date,  
                })
                new_record._compute_rgp()
                new_record._compute_totals()
                new_record._compute_revpar()
                new_record._compute_adr()
                new_record._compute_loyal_guests()
                new_record._compute_occupancy_rate()
                new_record._compute_trevpar()

            current_date += timedelta(days=1)



