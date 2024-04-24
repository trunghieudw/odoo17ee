import calendar
from typing import Dict, Tuple, Sequence, Any, List, NoReturn
from datetime import datetime, timedelta
from odoo import models, SUPERUSER_ID


class Purchase:
    @staticmethod
    def _find_partner(env, delivery_book_id: models) -> models:
        if delivery_book_id.carrier_id.delivery_type == 'viettelpost':
            vat = env['ir.config_parameter'].sudo().get_param('viettelpost_vat')
        elif delivery_book_id.carrier_id.delivery_type == 'ahamove':
            vat = env['ir.config_parameter'].sudo().get_param('ahamove_vat')
        else:
            return delivery_book_id.sender_id
        partner = env['res.partner'].sudo().search([('vat', '=', vat)], limit=1)
        return partner

    @staticmethod
    def _get_datetime() -> Sequence[str]:
        current_month, current_year = datetime.now().month, datetime.now().year
        days_in_month = calendar.monthrange(current_year, current_month)[1]
        start_datetime = f'{current_year:04d}-{current_month:02d}-01 00:00:00'
        end_datetime = f'{current_year:04d}-{current_month:02d}-{days_in_month} 23:59:59'
        return start_datetime, end_datetime

    @staticmethod
    def _get_purchase_order_line(delivery_book_id: models) -> List[Tuple[int, int, Dict[str, Any]]]:
        line_so_name = delivery_book_id.deli_order_id.sale_id.name
        line_book_create_date = delivery_book_id.create_date + timedelta(hours=7)
        line_bl_code = delivery_book_id.bl_code
        delivery_type = delivery_book_id.carrier_id.delivery_type
        return [(0, 0, {
            'product_id': delivery_book_id.carrier_id.product_id.id,
            'name': f'{line_so_name} - {line_book_create_date.strftime("%m/%d/%Y")} - {line_bl_code}',
            'price_unit': delivery_book_id.money_total if delivery_type == 'viettelpost' else delivery_book_id.fee_ship,
            'taxes_id': False
        })]

    @staticmethod
    def _get_picking_type(env, delivery_book_id: models) -> models:
        picking_type_id = env['stock.picking.type'].sudo().search([
            ('warehouse_id', '=', delivery_book_id.warehouse_id.id),
            ('sequence_code', 'in', ['IN', 'REC'])
        ])
        return picking_type_id

    @staticmethod
    def _get_purchasing_representative_user(env):
        user_id = env['ir.config_parameter'].sudo().get_param('purchasing_representative_user_id')
        return int(user_id)

    @staticmethod
    def _get_body_purchase_order(env, delivery_book_id, partner) -> Dict[str, Any]:
        picking_type_id = Purchase._get_picking_type(env, delivery_book_id)
        user_id = Purchase._get_purchasing_representative_user(env)
        body = {
            'company_id': delivery_book_id.deli_order_id.sale_id.company_id.id,
            'user_id': user_id,
            'picking_type_id': picking_type_id.id,
            'partner_id': partner.id,
            'state': 'draft',
            'order_line': Purchase._get_purchase_order_line(delivery_book_id)
        }
        return body

    @staticmethod
    def _get_body_check_code_history(env, delivery_book_id: models) -> Dict[str, Any]:
        partner = Purchase._find_partner(env, delivery_book_id)
        type_paid = delivery_book_id.deli_order_id.sale_id.payment_method
        body = {
            'so_code': delivery_book_id.deli_order_id.sale_id.id,
            'commitment_date': delivery_book_id.create_date,
            'shipper': partner.id,
            'type_paid': type_paid,
            'amount_residual': 0 if type_paid == 'online' else delivery_book_id.deli_order_id.sale_id.amount_due,
            'amount_paid': 0 if type_paid == 'online' else delivery_book_id.cod,
            'state': 'new',
            'x_studio_warehouse': delivery_book_id.warehouse_id.id
        }
        return body

    @staticmethod
    def create_check_cod_history(env, delivery_book_id):
        env['check.cod.history'].sudo().create(Purchase._get_body_check_code_history(env, delivery_book_id))

    @staticmethod
    def handle_purchase_order(env, delivery_book_id: models) -> NoReturn:
        env.uid = SUPERUSER_ID
        partner = Purchase._find_partner(env, delivery_book_id)
        start_datetime, end_datetime = Purchase._get_datetime()
        purchase_order = env['purchase.order'].sudo().search([
            ('company_id', '=', delivery_book_id.deli_order_id.sale_id.company_id.id),
            ('partner_id', '=', partner.id),
            ('create_date', '>=', start_datetime),
            ('create_date', '<=', end_datetime),
            ('state', '=', 'draft')
        ])
        if not purchase_order:
            env['purchase.order'].sudo().create(Purchase._get_body_purchase_order(env, delivery_book_id, partner))
        else:
            purchase_order.sudo().write({'order_line': Purchase._get_purchase_order_line(delivery_book_id)})
        if delivery_book_id.deli_order_id.sale_id.delivery_status == 'delivered':
            delivery_book_id.deli_order_id.sale_id.action_done()
        else:
            delivery_book_id.deli_order_id.sale_id.message_post(
                subject='Delivery update',
                boby=f"""
                    <p>Giao hàng thành công</p>
                    <ul>
                        <li>Shipping method: {delivery_book_id.sender_id.name if delivery_book_id.carrier_id.delivery_type == 'deli_boys' else delivery_book_id.carrier_id.delivery_type}</li>
                        <li>Tracking link: {delivery_book_id.tracking_link}</li>
                    </ul>
                """
            )
        Purchase.create_check_cod_history(env, delivery_book_id)