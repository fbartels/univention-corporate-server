<?php
/**
 * The Auth_pam:: class provides a PAM-based implementation of the Horde
 * authentication system.
 * 
 * PAM (Pluggable Authentication Modules) is a flexible mechanism for
 * authenticating users.  It has become the standard authentication system for
 * Linux, Solaris and FreeBSD.
 *
 * This implementation requires Chad Cunningham's pam_auth extension:
 *
 *      http://www.math.ohio-state.edu/~ccunning/pam_auth/
 *
 * Optional parameters:
 * ====================
 *   'service'  --  The name of the PAM service to use when authenticating.
 *                  DEFAULT: php
 *
 *
 * $Horde: framework/Auth/Auth/pam.php,v 1.3 2004/05/25 08:50:11 mdjukic Exp $
 *
 * Copyright 2004 Jon Parise <jon@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Parise <jon@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class Auth_pam extends Auth
{
    /**
     * An array of capabilities, so that the driver can report which
     * operations it supports and which it doesn't.
     *
     * @var array $capabilities
     */
    var $capabilities = array('add'           => false,
                              'update'        => false,
                              'resetpassword' => false,
                              'remove'        => false,
                              'list'          => false,
                              'transparent'   => false);

    /**
     * Constructs a new PAM authentication object.
     *
     * @access public
     *
     * @param optional array $params  A hash containing connection parameters.
     */
    function Auth_pam($params = array())
    {
        $this->_params = $params;
        if (!empty($params['service'])) {
            ini_set('pam_auth.servicename', $params['service']);
        }

        if (!extension_loaded('pam_auth')) {
            dl('pam_auth.so');
        }
    }

    /**
     * Find out if a set of login credentials are valid.
     *
     * @access private
     *
     * @param string $userId      The userId to check.
     * @param array $credentials  An array of login credentials.
     *
     * @return boolean  Whether or not the credentials are valid.
     */
    function _authenticate($userId, $credentials)
    {
        if (empty($credentials['password'])) {
            Horde::fatal(PEAR::raiseError(_("No password provided for Login authentication.")), __FILE__, __LINE__);
        }

        if (!extension_loaded('pam_auth')) {
            Horde::fatal(PEAR::raiseError(_("PAM authentication is not available.")), __FILE__, __LINE__);
        }

        if (!pam_auth($userId, $credentials['password'], &$error)) {
            $this->_setAuthError(AUTH_REASON_MESSAGE, $error);
            return false;
        }

        return true;
    }
}
