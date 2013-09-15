<?php
	/*
	 * This file is part of the openerplib.
	 *
	 * (c) Benito Rodriguez <brarcos@gmail.com>
	 * 
	 * https://github.com/b3ni/openerplib
	 *
	 * For the full copyright and license information, please view the LICENSE
	 * file that was distributed with this source code.
	 */
	if (isset($_POST['db'])){
    
	define('_OPENERPLIB_BD_', $_POST['db']);
  	define('_OPENERPLIB_UID_', connect());
  	define('_OPENERPLIB_PASSWD_', $_POST['password']);
    }
    else
    {
	define('_OPENERPLIB_BD_', '');
  	define('_OPENERPLIB_UID_', 0);
  	define('_OPENERPLIB_PASSWD_', '');    
    }
  	define('_OPENERPLIB_URL_', 'http://localhost:8069/xmlrpc');
?>