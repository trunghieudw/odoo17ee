from werkzeug.utils import redirect
from odoo.http import Controller, route


class Main(Controller):
    @route('/sign/help', auth='public')
    def open_web_fs(self):
        return redirect('https://friendshipcakes.com/hdkyonline')
