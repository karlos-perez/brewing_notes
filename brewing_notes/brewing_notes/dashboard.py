# -*- coding: utf-8 -*-

from grappelli.dashboard import modules, Dashboard


class BrewDashboard(Dashboard):
    """
    Custom index dashboard for www.
    """

    def __init__(self, **kwargs):
        Dashboard.__init__(self, **kwargs)
        # site_name = get_admin_site_name(context)

        self.children.append(modules.AppList(
            title='Brewing_notes',
            column=1,
            collapsible=True,
            models=('catalog.*'),
            exclude=('nnmware.core.*',)
        ))
        self.children.append(modules.AppList(
            title='System',
            column=1,
            collapsible=True,
            css_classes=('grp-closed',),
            models=('django.contrib.*', 'nnmware.core.*', 'nnmware.core.models.VisitorHit')
        ))
        # append a recent actions module
        self.children.append(modules.RecentActions(
            'Recent Actions',
            limit=10,
            column=2,
        ))

        # append another link list module for "support".
        self.children.append(modules.LinkList(
            'Brewing notes site',
            column=3,
            children=[
                {
                    'title': 'Main Page',
                    'url': '/',
                    'external': False,
                },
                {
                    'title': 'Admin page',
                    'url': '/bossmode/',
                    'external': False,
                },
            ]
        ))


