from odoo import models, fields, api, _
import re
from odoo.exceptions import ValidationError
import pickle
import os
import pandas as pd
import numpy as np
import sklearn
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from datetime import datetime, date

import logging
_logger = logging.getLogger(__name__)

class HotelGuest(models.Model):
    _name = 'hotel.guest'
    _description = 'Hotel Guest'
    _rec_name = 'guest_id'

    first_name = fields.Char(string='First Name', required=True)
    last_name = fields.Char(string='Last Name', required=True)
    guest_id = fields.Char(string='Full Name', compute='_compute_name', store=True)
    email = fields.Char(string='Email')
    number = fields.Char(string='Phone Number')
    age = fields.Integer(string='Age', required=True)
    parent_id = fields.Many2one('hotel.guest', string='Parent/Guardian')
    child_ids = fields.One2many('hotel.guest', 'parent_id', string='Children')
    nin = fields.Char(string="NIN")  
    country_state = fields.Many2one("res.country.state", string="State")
    country = fields.Many2one('res.country', string="Country", ondelete='restrict')
    reserv_ids = fields.One2many(
        'hotel.reservation', 
        'guest_id', 
        string='Reservations', 
        readonly=True,
        domain=[('state', 'not in', ['draft', 'cancel'])] 
    )
    remaining_healthspan = fields.Integer(string='Remaining Healthspan', compute='_compute_remaining_healthspan')

    # CRM-Specific Attributes
    previous_reservations = fields.Integer(string='Previous Reservations', default=0, compute='_compute_previous_reservations')
    loyalty_status = fields.Boolean(string='Loyal', default=False)
    average_spend_per_stay = fields.Monetary(string='Average Spend Per Visit', currency_field='currency_id', compute='_compute_average_spend_per_stay')
    annual_stay_frequency = fields.Integer(string='Annual Stay Frequency', compute='_compute_annual_stay_frequency')
    remaining_healthspan = fields.Integer(string='Remaining Healthspan', compute='_compute_remaining_healthspan')
    clv = fields.Monetary(string='Customer Lifetime Value', currency_field='currency_id', compute='_compute_clv')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    
    # Computed Fields
    @api.depends('average_spend_per_stay', 'annual_stay_frequency', 'remaining_healthspan', 'clv')
    def update_loyalty_status(self):
        model_path = os.path.join(os.path.dirname(__file__), 'gb_model.pkl')
        _logger.info(f"Loading model from {model_path}")

        try:
            with open(model_path, 'rb') as model_file:
                model = CustomUnpickler(model_file).load()
        except Exception as e:
            _logger.error(f"Error loading model: {e}")
            return

        guests = self.env['hotel.guest'].search([])
        _logger.info(f"Number of guests to process: {len(guests)}")

        if not guests:
            _logger.info("No guests found")
            return

        # Collect guest data into a DataFrame
        guest_data = [{
            'id': guest.id,
            'average_spend_per_stay': guest.average_spend_per_stay,
            'annual_stay_frequency': guest.annual_stay_frequency,
            'remaining_healthspan': guest.remaining_healthspan,
            'clv': guest.clv
        } for guest in guests]
        
        df_guests = pd.DataFrame(guest_data)
        
        # Ensure only the model features are selected
        feature_columns = ['average_spend_per_stay', 'annual_stay_frequency', 'remaining_healthspan', 'clv']
        df_features = df_guests[feature_columns]

        _logger.info(f"Guest features before scaling: {df_features}")

        # Apply StandardScaler
        scaler = StandardScaler()
        try:
            df_features_scaled = scaler.fit_transform(df_features)
        except Exception as e:
            _logger.error(f"Error during scaling: {e}")
            return

        _logger.info(f"Guest features after scaling: {df_features_scaled}")

        # Make predictions
        try:
            predictions = model.predict(df_features_scaled)
        except Exception as e:
            _logger.error(f"Error predicting loyalty status: {e}")
            return

        # Update loyalty status for each guest
        for idx, guest in enumerate(guests):
            try:
                is_loyal = predictions[idx]
                _logger.info(f"Predicted loyalty status for guest ID {guest.id}: {is_loyal}")
                guest.loyalty_status = is_loyal
            except Exception as e:
                _logger.error(f"Error updating loyalty status for guest ID {guest.id}: {e}")

    @api.depends('first_name', 'last_name')
    def _compute_name(self):
        for guest in self:
            if not guest.first_name or not guest.last_name:
                guest.guest_id = ''
                continue
            base_name = f"{guest.first_name} {guest.last_name}"
            # Check if the record exists in the database
            existing_guests = self.env['hotel.guest'].search([('guest_id', '=', base_name)])
            # Exclude the current record if it already exists
            existing_guests -= guest
            if existing_guests:
                guest.guest_id = f"{base_name} ({len(existing_guests) + 1})"
            else:
                guest.guest_id = base_name

    @api.depends('reserv_ids')
    def _compute_previous_reservations(self):
        for guest in self:
            guest.previous_reservations = len(guest.reserv_ids)

    @api.depends('reserv_ids')
    def _compute_average_spend_per_stay(self):
        for guest in self:
            if guest.reserv_ids:
                guest.average_spend_per_stay = sum(guest.reserv_ids.mapped('total_price')) / len(guest.reserv_ids)
            else:
                guest.average_spend_per_stay = 0


    @api.depends('reserv_ids')
    def _compute_annual_stay_frequency(self):
        for guest in self:
            today = date.today()
            reservations_this_year = guest.reserv_ids.filtered(lambda r: r.check_in_date.year == today.year)
            guest.annual_stay_frequency = len(reservations_this_year)

    @api.depends('average_spend_per_stay', 'annual_stay_frequency', 'remaining_healthspan')  
    def _compute_clv(self):
        for guest in self:
            guest.clv = (
                guest.average_spend_per_stay * 
                guest.annual_stay_frequency * 
                guest.remaining_healthspan
            )


    # Remaining Healthspan Calculation
    @api.depends('age')
    def _compute_remaining_healthspan(self):
        for guest in self:
            if guest.age:
                average_lifespan = 75  # Example
                guest.remaining_healthspan = max(0, average_lifespan - guest.age)
            else:
                guest.remaining_healthspan = 0


    @api.model
    def create(self, vals):
        if vals.get('email'):
            match = re.match(r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', vals.get('email'))
            if match is None:
                raise ValidationError('Not a valid E-mail ID')

        if vals.get('number'):
            match = re.match(r'\+{0,1}[0-9]{10,12}', vals.get('number'))
            if match is None:
                raise ValidationError('Invalid Phone Number')

        if vals.get('age'):
            if vals.get('age') < 18 and not vals.get('parent_id'):
                raise ValidationError(_("A parent/guardian is required for guests under 18."))
            if vals.get('age') >= 18 and not vals.get('email') and not vals.get('number') and not vals.get('nin'):
                raise ValidationError(_("Email, Phone Number, and NIN (National Identification Number) are required for guests over 18."))

        return super(HotelGuest, self).create(vals)
    

class CustomUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module == 'sklearn.ensemble._gb_losses':
            return sklearn.ensemble.GradientBoostingClassifier
        return super().find_class(module, name)
