<?php
/**
 * The Horde_RPC_xmlrpc class provides an XMLRPC implementation of the
 * Horde RPC system.
 *
 * $Horde: framework/RPC/RPC/xmlrpc.php,v 1.8 2004/04/08 20:45:11 jan Exp $
 *
 * Copyright 2002-2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_RPC
 */
class Horde_RPC_xmlrpc extends Horde_RPC {

    /**
     * Resource handler for the XMLRPC server.
     * @var object $_server
     */
    var $_server;

    /**
     * XMLRPC server constructor
     *
     * @access private
     * @return object   A RPC server instance
     */
    function Horde_RPC_xmlrpc()
    {
        parent::Horde_RPC();

        $this->_server = xmlrpc_server_create();

        foreach ($GLOBALS['registry']->listMethods() as $method) {
            xmlrpc_server_register_method($this->_server, str_replace('/', '.', $method), array('Horde_RPC_xmlrpc', '_dispatcher'));
        }
    }

    /**
     * Cleans up the RPC server.
     */
    function shutdown()
    {
        xmlrpc_server_destroy($this->_server);
    }

    /**
     * Sends an RPC request to the server and returns the result.
     *
     * @param string    The raw request string.
     *
     * @return string   The XML encoded response from the server.
     */
    function getResponse($request)
    {
        $response = null;
        return xmlrpc_server_call_method($this->_server, $request, $response);
    }

    /**
     * Will be registered as the handler for all available methods
     * and will call the appropriate function through the registry.
     *
     * @access private
     *
     * @param string $method    The name of the method called by the RPC request.
     * @param array $params     The passed parameters.
     * @param mixed $data       Unknown.
     *
     * @return mixed            The result of the called registry method.
     */
    function _dispatcher($method, $params, $data)
    {
        global $registry;
        $method = str_replace('.', '/', $method);

        if (!$registry->hasMethod($method)) {
            return sprintf(_("Method '%s' is not defined"), $method);
        }

        return $registry->call($method, $params);
    }

    /**
     * Builds an XMLRPC request and sends it to the XMLRPC server.
     *
     * This statically called method is actually the XMLRPC client.
     *
     * @param string $url       The path to the XMLRPC server on the called host.
     * @param string $method    The method to call.
     * @param array $params     (optional) A hash containing any necessary
     *                          parameters for the method call.
     * @param $options  Optional associative array of parameters which can be:
     *                  user           - Basic Auth username
     *                  pass           - Basic Auth password
     *                  proxy_host     - Proxy server host
     *                  proxy_port     - Proxy server port
     *                  proxy_user     - Proxy auth username
     *                  proxy_pass     - Proxy auth password
     *                  timeout        - Connection timeout in seconds.
     *                  allowRedirects - Whether to follow redirects or not
     *                  maxRedirects   - Max number of redirects to follow
     *
     * @return mixed            The returned result from the method or a PEAR
     *                          error object on failure.
     */
    function request($url, $method, $params = null, $options = array())
    {
        $options['method'] = 'POST';
        $language = isset($GLOBALS['language']) ? $GLOBALS['language'] :
                    (isset($_SERVER['LANG']) ? $_SERVER['LANG'] : '');

        if (!isset($options['timeout'])) {
            $options['timeout'] = 5;
        }
        if (!isset($options['allowRedirects'])) {
            $options['allowRedirects'] = true;
            $options['maxRedirects'] = 3;
        }

        require_once 'HTTP/Request.php';

        $http = &new HTTP_Request($url, $options);
        if (!empty($language)) {
            $http->addHeader('Accept-Language', $language);
        }
        $http->addHeader('User-Agent', 'Horde RPC client');
        $http->addHeader('Content-Type', 'text/xml');
        $http->addRawPostData(xmlrpc_encode_request($method, $params));

        $result = $http->sendRequest();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        } elseif ($http->getResponseCode() != 200) {
            return PEAR::raiseError(_("Request couldn't be answered. Returned errorcode: ") . $http->getResponseCode(), 'horde.error');
        } elseif (!strstr($http->getResponseBody(), '<?xml')) {
            return PEAR::raiseError(_("No valid XML data returned"), 'horde.error', null, null, $http->getResponseBody());
        } else {
            $response = @xmlrpc_decode(substr($http->getResponseBody(), strpos($http->getResponseBody(), '<?xml')));
            if (is_array($response) && isset($response['faultString'])) {
                return PEAR::raiseError($response['faultString'], 'horde.error');
            } elseif (is_array($response) && isset($response[0]) &&
                      is_array($response[0]) && isset($response[0]['faultString'])) {
                return PEAR::raiseError($response[0]['faultString'], 'horde.error');
            }
            return $response;
        }
    }

}
