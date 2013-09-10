# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

####believe we get these from sql that we are subclassing
#from keystone.common import dependency
#from keystone.common import sql
#from keystone.common.sql import migration
#from keystone.common import utils
#from keystone import exception
#from keystone import identity

from keystone import config
from keystone.common import logging
from keystone.identity.backends import sql

import ldap

# additions for exception config file
import json
usersConf = open("/etc/keystone/comcastkeystone.conf")
userVars = json.load(usersConf)
usersConf.close()

CONF = config.CONF
LOG = logging.getLogger(__name__)

###Unsure if this is depricated with grizzly so left it in for now since its inherited until I figure it out
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

    def _check_password(self, password, user_ref):
        """Check the specified password against the data store.

        This is modeled on ldap/core.py.  The idea is to make it easier to
        subclass Identity so that you can still use it to store all the data,
        but use some other means to check the password.
        Note that we'll pass in the entire user_ref in case the subclass
        needs things like user_ref.get('name')
        For further justification, please see the follow up suggestion at
        https://blueprints.launchpad.net/keystone/+spec/sql-identiy-pam

        """
        
        # Authenticate against LDAP
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        conn = ldap.initialize(self.LDAP_URL)
        conn.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
        conn.set_option(ldap.OPT_REFERRALS, 0)
        conn.set_option(ldap.OPT_X_TLS,ldap.OPT_X_TLS_DEMAND)
        conn.set_option(ldap.OPT_X_TLS_DEMAND, True )
        try:
            conn.simple_bind_s(domain_user_name, password)
        except ldap.LDAPINVALID_CREDENTIALS:
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

