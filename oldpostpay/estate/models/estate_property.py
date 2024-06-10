# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Real Estate Property"
    _order = "sequence"

    name = fields.Char('Property Name', required=True, translate=True)
    number_of_rooms = fields.Integer('# Room', required=True)
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=10)

    _sql_constraints = [
        ('check_number_of_rooms', 'CHECK(number_of_rooms >= 0)', 'The number of Rooms can\'t be negative.'),
    ]