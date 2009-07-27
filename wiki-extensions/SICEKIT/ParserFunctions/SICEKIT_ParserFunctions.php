<?php
/*
 This file is part of SICEKIT, http://oss.inqnet.at/trac/sicekit.
 SICEKIT CSS Extension
 Copyright (c) 2009 SICEKIT Development Team.
*/

if (!defined('MEDIAWIKI')) {
        die(-1);
}

$wgExtensionCredits['parserhook'][] = array(
        'name'         => 'SICEKIT: ParserFunctions',
        'version'      => '0.0',
        'author'       => 'SICEKIT Development Team <team@sicekit.org>', 
        'url'          => 'http://sicekit.org',
        'description'  => 'Enhances the parser with SICEKIT specific functions'
);

require("extensions/SICEKIT/ParserFunctions/ContractRef.php");
require("extensions/SICEKIT/ParserFunctions/GoogleMapEmbed.php");
require("extensions/SICEKIT/ParserFunctions/Monitoring.php");
