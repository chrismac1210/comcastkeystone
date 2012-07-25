ComcastKeystone - Comcast specific implementations of OpenStack Keystone functionality.

Note: This implementation overrides and extends OpenStack Keystone functionality but does not replace it.
    As such it should be installed in addition to the OpenStack Keystone package.

Identity: comcastkeystone.identity.backends.ldapsql
    Why:
        Comcast requires OpenStack users be authenticated against the corporate LDAP servers. OpenStack's
        Keystone security module supports LDAP integration via keystone.identity.backends.ldap/core.py.

        The problem with this implementation is that it assume that if you're using LDAP for authentication
        then you're using LDAP for authorization. This requires having Keystone's schema into Comcast's
        corporate LDAP. NOT gonna happen.

        So what we want is to authenticate against the corporate LDAP but authorize against access rules
        defined in the Keystone database.

    How:
        In searching for a solution the following was found on Keystone's launchpad answers site
        (https://answers.launchpad.net/keystone/+question/188701):

            "Joseph Heck (heckj) said on 2012-03-06:
                You can get a high level overview of how Keystone is put together at
             http://keystone.openstack.org/architecture.html, and the piece I'm
             specifically suggesting you make a backend for is the "Identity"
             keystone-internal-service. For the code side, I'd recommend looking
             in keystone/identity/core.py - the specifically subclassing the
             Driver class in there. (See keystone/identity/backends/*.py for
             examples)."

    So:
        That's what we did.

    What:
        Comcast has only one production LDAP server. There is no test or development instance to connect to.
        In some environments(the Lab for instance) access to the production LDAP server is not possible. For
        this reason its possible to configure the comcastkeystone.identity.backends.ldapsql to
        authenticate using either LDAP or the native Keystone SQL implementation.

    Configuration:
        Service configuration
            OpenStack is composed of several services each of which must authenticate via Keystone (the
            security service). This is supported by configuring all the services with the same "admin_token"
            value. The following is a list of files in which this must be set:
                /etc/glance/glance-api-paste.ini
                /etc/glance/glance-registry-paste.ini
                /etc/nova/api-paste.ini
                /etc/keystone/keystone.conf
                /etc/swift/proxy-server.conf

            NOTE: A userid/password scheme for service authentication is also supported but in our case the
            service users (nova, glance, swift, keystone) will not have LDAP credentials. For this reason it
            is important that the following settings be either commented out or removed from the above files:
                admin_user
                admin_password

        User Creation
            Keystone user accounts will need to be created for every user that will need to access the
            OpenStack web Dashboard or the command line tools. The user names for those accounts must match
            the user's LDAP user name.

        RPM Install
            Note that this RPM will be installed alongside the OpenStack Keystone RPM. It is not a replacement.

        Keystone configuration
            Configuration is accomplished by altering values in the Keystone configuration file. This file is
            typically located at:
                /etc/keystone/keystone.conf

            NOTE: That one of the following two methods must be chosen.

            LDAP Authentication (Production)
                The following settings indicate the Comcast LDAP implementation should be used.
                    [identity]
                    driver = comcastkeystone.identity.backends.ldapsql.LdapIdentity

                    [ldap]
                    url = ldap://adapps.cable.comcast.com:389
                    user_tree_dn = cable

            SQL Authentication (dev, Lab and other environments which cannot access the LDAP server)
                The following settings indicate the native Keystone SQL implementation should be used.
                    [identity]
                    driver = comcastkeystone.identity.backends.ldapsql.SqlIdentity

                    [sql]
                    connection = mysql://<Keystone DB Admin User Name>:<Keystone DB Admin User Password>@<DB Host>/keystone?charset=utf8


