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


    Testing:
        As mentioned in the "Configuration - Keystone configuration" section above there are two ways to configure
        Authentication. SQL Authentication relies on the Keystone's native facilities which uses a MySql database as its
        datastore. The other, LDAP Authentication, implements authentication against Comcast's corporate LDAP server
        which poses an addtitional challenge.

        The challenge is that the LDAP server is a production server. The "Lab" environment has NO CONNECTIVITY to it.
        This means is that to test this method you first follow the directions in the "Configuration - Keystone
        configuration - LDAP Authentication" section. Then you must set up SSH tunneling to allow a connection to the
        LDAP server through a machine that has access to it.

        SQL Authentication Testing
            Configuration:
                Follow the instructions in the "Configuration - Keystone configuration - SQL Authentication" section.

            Restart Keystone:
                As "root" enter the following at the command prompt:
                    [root@devstack01 init.d]# service openstack-keystone restart

            Testing:
                Then follow the "Test Script" below.

        LDAP Authentication Testing
            Configuration:
                - SSH Tunneling (NOTE: NOT required for production):
                    You need a machine that can access the Production LDAP server. This is not hard to find. Any
                    machine with a wired ethernet connection at Comcast Center should work. To verify that the
                    machine can connect use telnet. It should go something like this:

                        you@yourMachine ~ $ telnet adapps.cable.comcast.com 389
                        Trying 147.191.115.15...
                        Connected to adapps.g.comcast.com.
                        Escape character is '^]'.

                    Next you need to establish the SSH Tunnel via remote port forwarding. To do that enter the
                    following command:

                        you@yourMachine ~ $ ssh -R localhost:3389:adapps.cable.comcast.com:389 red@10.253.183.20

                    You will be prompted for a password. Then you should be able to verify connectivity to the LDAP
                    server via telnet:

                        [red@devstack01 ~]$ telnet localhost 3389
                        Trying ::1...
                        Connected to localhost.
                        Escape character is '^]'.

                - Follow the instructions in the "Configuration - Keystone configuration - LDAP Authentication" section
                    but for testing there is one small change. The value for the "url" in the LDAP section is different.
                    It should be:
                        [ldap]
                        url = ldap://localhost:3389
                        user_tree_dn = cable

            Restart Keystone:
                As "root" enter the following at the command prompt:
                    [root@devstack01 init.d]# service openstack-keystone restart

            Testing:
                Then follow the "Test Script" below.

        Test Script
            - Connect to the OpenStack Dashboard (Horizon)
            - Enter your user ID
            - Enter you password
                - Note: For SQL Authentication this is likely the standard lab password. For LDAP Authentication it will
                    be the password you use to logon to most corporate apps like email and Commons.
            - You should given access to the OpenStack Dashboard (Horizon):
                - If so:  PASS
                - If not: FAIL




