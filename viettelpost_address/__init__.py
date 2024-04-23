from odoo import tools

from . import models


def _install_init_data(env):
    tools.convert_file(env,
                       'viettelpost_address',
                       'data/res.city.csv',
                       None,
                       mode='init',
                       noupdate=True,
                       kind='init')
