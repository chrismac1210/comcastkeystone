# vim: tabstop=4 shiftwidth=4 softtabstop=4

#   Comcast requires OpenStack users be authenticated against the corporate LDAP servers. OpenStack's
#   Keystone security module supports LDAP integration via keystone.identity.backends.ldap/core.py.
#
#   The problem with this implementation is that it assume that if you're using LDAP for authentication
#   then you're using LDAP for authorization. This requires having Keystone's schema into Comcast's
#   corporate LDAP. NOT gonna happen.
#
#   So what we want is to authenticate against the corporate LDAP but authorize against access rules
#   defined in the Keystone database.
#
#   That's what this module does. It overrides the Identity class so that LDAP handles authentication
#   and Keystone does the rest (roles, tenants, etc)

# Required by 'Original sql authentication logic'
#from nevow.livepage import self
from keystone.common import utils

from keystone import config
from keystone.common import logging
from keystone.identity.backends import sql

import ldap

CONF = config.CONF
LOG = logging.getLogger(__name__)

class SqlIdentity(sql.Identity):
    def __init__(self):
        LOG.debug("Authentication will be performed via: %s", self)
        super(SqlIdentity, self).__init__()

class LdapIdentity(sql.Identity):
    def __init__(self):
        LOG.debug("Authentication will be performed via: %s", self)
        super(LdapIdentity, self).__init__()
        self.LDAP_URL = CONF.ldap.url
        self.LDAP_DOMAIN = CONF.ldap.user_tree_dn

    # Identity interface
    def authenticate(self, user_id=None, tenant_id=None, password=None):
        """Authenticate based on a user, tenant and password.

        Expects the user object to have a password field and the tenant to be
        in the list of tenants on the user.


        """
        # If they're not in keystone no need to check LDAP
        user_ref = self._get_user(user_id)
        if (not user_ref):
            raise AssertionError('User not registered in Keystone')

        # We were given the id of the user in the keystone database.
        user_name = user_ref.get('name')

        # If its an OpenStack service call validate against the native Keystone implementation because the service
        # users will NOT be in LDAP
        if user_name in ['glance', 'nova', 'swift', 'admin']:
            return super(LdapIdentity, self).authenticate(user_id, tenant_id, password)

        # We need the user name. Get it (prepend domain name (yes, a Hack))
        domain_user_name = self.LDAP_DOMAIN + '\\' + user_ref.get('name')
        LOG.debug("Attempting to validate user with name: %s", domain_user_name)

        # Authenticate against LDAP
        conn = ldap.initialize(self.LDAP_URL)
        conn.protocol_version = 3
        conn.set_option(ldap.OPT_REFERRALS, 0)
        try:
            conn.simple_bind_s(domain_user_name, password)
        except ldap.LDAPError:
            raise AssertionError('Invalid user / password')

        tenants = self.get_tenants_for_user(user_id)
        if tenant_id and tenant_id not in tenants:
            raise AssertionError('Invalid tenant')

        tenant_ref = self.get_tenant(tenant_id)
        if tenant_ref:
            metadata_ref = self.get_metadata(user_id, tenant_id)
        else:
            metadata_ref = {}
        return (sql._filter_user(user_ref), tenant_ref, metadata_ref)

