import logging

from odoo.addons.viettelpost_address.models.viettelpost_request import ViettelPostRequest as ViettelPostRequestBase

from odoo import _, fields

_logger = logging.getLogger(__name__)


class ViettelPostRequest(ViettelPostRequestBase):
    def check_required_value(self, carrier, order, ship_from, ship_to):
        required_field = {'city_id': 'City', 'district_id': 'District', 'phone': 'Phone'}
        # Check required field for sender
        res = [required_field[field] for field in required_field if not ship_from[field]]
        if res:
            return _('The address of your company is missing or wrong.\n(Missing field(s) : %s)', ','.join(res))
        # Check required field for receiver
        res = [required_field[field] for field in required_field if not ship_to[field]]
        if res:
            return _('The address of your receiver is missing or wrong.\n(Missing field(s) : %s)', ','.join(res))
        return False

    def _get_shipping_payload(self, carrier, order, ship_from, ship_to):
        weight_value = carrier._viettelpost_convert_weight(order._get_estimated_weight())
        payload = {
            'PRODUCT_WEIGHT': weight_value,
            'PRODUCT_PRICE': order.currency_id._convert(order.amount_total, carrier.currency_id, order.company_id, order.date_order or fields.Date.today()),
            'MONEY_COLLECTION': 0,
            'ORDER_SERVICE': carrier.viettelpost_default_service_type,
            'SENDER_PROVINCE': ship_from.city_id.viettelpost_province_id,
            'SENDER_DISTRICT': ship_from.district_id.viettelpost_district_id,
            'RECEIVER_PROVINCE': ship_to.city_id.viettelpost_province_id,
            'RECEIVER_DISTRICT': ship_to.district_id.viettelpost_district_id,
            'PRODUCT_TYPE': carrier.viettelpost_product_type,
            'NATIONAL_TYPE': carrier.viettelpost_national_type,
        }
        return payload

    def get_shipping_price(self, carrier, order, ship_from, ship_to):
        client = self._set_client()
        self._add_security_header(client)
        payload = self._get_shipping_payload(carrier, order, ship_from, ship_to)
        response = self._request(client, self.endurl + 'order/getPrice', method='post', json=payload)
        return response

    def viettelpost_shipping_data(self, carrier, order, ship_from, ship_to, picking):
        list_item = []
        payload = self._get_shipping_payload(carrier, order, ship_from, ship_to)

        for line in picking.move_lines:
            product_price = line.product_id.lst_price
            if order.currency_id != carrier.currency_id:
                price = order.currency_id._convert(product_price, carrier.currency_id, order.company_id, order.date_order or fields.Date.today())
            else:
                price = product_price
            item = {'PRODUCT_NAME': line.product_id.name, 'PRODUCT_PRICE': price, 'PRODUCT_WEIGHT': carrier._viettelpost_convert_weight(line.product_id.weight), 'PRODUCT_QUANTITY': line.product_uom_qty}
            list_item.append(item)

        payload['LIST_ITEM'] = list_item
        payload['ORDER_SERVICE'] = picking.viettelpost_default_service_type
        payload['RECEIVER_PHONE'] = ship_to.phone
        payload['SENDER_PHONE'] = ship_from.phone
        payload['RECEIVER_ADDRESS'] = ship_to.partner_address
        payload['RECEIVER_FULLNAME'] = ship_to.name
        payload['SENDER_ADDRESS'] = ship_from.partner_address
        payload['SENDER_FULLNAME'] = ship_from.name
        payload['ORDER_PAYMENT'] = picking.viettelpost_order_payment
        payload['GROUPADDRESS_ID'] = picking.viettelpost_store_id.group_address_id
        payload['PRODUCT_NAME'] = order.name
        payload['PRODUCT_PRICE'] = order.currency_id._convert(order.amount_total, carrier.currency_id, order.company_id, order.date_order or fields.Date.today())
        return payload

    def send_shipping(self, carrier, order, ship_from, ship_to, picking):
        check_result = self.check_required_value(carrier, order, ship_from, ship_to)
        if check_result:
            raise UserError(check_result)

        if not ship_to.phone:
            raise UserError('Partner phone is required')

        client = self._set_client()
        self._add_security_header(client)
        payload = self.viettelpost_shipping_data(carrier, order, ship_from, ship_to, picking)
        _logger.info(payload)
        response = self._request(client, self.endurl + 'order/createOrder', method='post', json=payload)
        if response.get('error_message'):
            raise UserError(response.get('error_message'))

        return response

    def return_label(self):
        pass

    def process_shipment(self):
        pass

    def cancel_shipment(self, tracking_number: int):
        client = self._set_client()
        self._add_security_header(client)
        payload = {'TYPE': 4, 'ORDER_NUMBER': tracking_number, 'NOTE': 'Ghi chú'}
        response = self._request(client, self.endurl + 'order/UpdateOrder', method='post', json=payload)
        if response.get('error_message'):
            raise UserError(response.get('error_message'))

    def get_access_token(self, username: str, password: str):
        client = self._set_client()
        self._add_security_header(client)
        payload = {'USERNAME': username, 'PASSWORD': password}
        response = self._request(client, self.endurl + 'user/Login', method='post', json=payload)
        return response

    def get_link_print(self, tracking_number: int, print_token: str):
        client = self._set_client()
        self._add_security_header(client)
        payload = {'TYPE': 1, 'ORDER_ARRAY': [tracking_number], 'PRINT_TOKEN': print_token}
        response = self._request(client, self.endurl + 'order/encryptLinkPrint', method='post', json=payload)
        return response

    def get_stores(self):
        client = self._set_client()
        self._add_security_header(client)
        response = self._request(client, self.endurl + 'user/listInventory', method='get')
        return response
