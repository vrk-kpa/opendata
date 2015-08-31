import logging

from ckan.lib.base import h, BaseController, render, abort, request
from ckan.plugins import toolkit
from ckan.common import c
log = logging.getLogger(__name__)

class YtpRequestController(BaseController):

    def new(self):

        context = {'model': model, 'user': c.user}

        return render("request/new.html")

    def mylist(self):
        """" Controller for listing own members requests (possibility to cancel and view current status)"""
        context = {'user': c.user or c.author}
        try:
            own_requests = toolkit.get_action('member_requests_mylist')(context, {})
            extra_vars = {'own_requests': own_requests}
            return render('request/mylist.html', extra_vars=extra_vars)
        except toolkit.NotAuthorized:
            abort(401, self.not_auth_message) 

    
    def list(self):
        """ Controller for listing member requests to be approved by admins"""
        context = {'user': c.user or c.author}
        try:
            member_requests = toolkit.get_action('member_requests_list')(context, {})
            extra_vars = {'member_requests': member_requests}
            return render('request/list.html', extra_vars=extra_vars)
        except toolkit.NotAuthorized:
            abort(401, self.not_auth_message)