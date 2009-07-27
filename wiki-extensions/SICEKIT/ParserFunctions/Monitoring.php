<?php
/*
 This file is part of SICEKIT, http://sicekit.org/trac/sicekit.
 SICEKIT CSS Extension
 Copyright (c) 2009 SICEKIT Development Team.
*/

if (!defined('MEDIAWIKI')) {
        die(-1);
}

//Avoid unstubbing $wgParser on setHook() too early on modern (1.12+) MW versions, as per r35980
if (defined('MW_SUPPORTS_PARSERFIRSTCALLINIT')) {
        $wgHooks['ParserFirstCallInit'][] = 'SICEKIT_ParserFunctions_Monitoring_Setup';
} else { // Otherwise do things the old fashioned way
        $wgExtensionFunctions[] = 'SICEKIT_ParserFunctions_Monitoring_Setup';
}

$wgHooks['LanguageGetMagic'][] = 'SICEKIT_ParserFunctions_Monitoring_Magic';

function SICEKIT_ParserFunctions_Monitoring_Setup() {
        global $wgParser, $SICEKIT_ParserFunctions_Monitoring_Config;
        $wgParser->setFunctionHook('monitoring', 'SICEKIT_ParserFunctions_Monitoring_Render', SFH_NO_HASH);
	if (!defined($SICEKIT_ParserFunctions_Monitoring_Config) or !is_array($SICEKIT_ParserFunctions_Monitoring_Config)) {
		$SICEKIT_ParserFunctions_Monitoring_Config = array(
			'server' => array(
				'nagios' => array(
					'desc' => 'Nagios',
					'url' => 'http://sicekit.org/example/nagios2/cgi-bin/status.cgi?navbarsearch=1&host=%HOSTNAME%',
				),
				'munin' => array(
					'desc' => 'Munin',
					'url' => 'http://sicekit.org/example/munin/cgi-bin/munin-find-by-name?host=%FQDN%',
				),
			),
			'switch' => array(
				'nagios' => array(
					'desc' => 'Nagios',
					'url' => 'http://sicekit.org/example/nagios2/cgi-bin/status.cgi?navbarsearch=1&host=%HOSTNAME%',
				),
				'torrus' => array(
					'desc' => 'Torrus',
					'url' => 'http://sicekit.org/example/torrus/snmp?path=%2FRouters%2F%FQDN%%2FInterface_Counters%2F',
				),
			),
			'switchport' => array(
				'torrus' => array(
					'desc' => '%ARG1%',
					'url' => 'http://sicekit.org/example/torrus/snmp?path=%2FRouters%2F%FQDN%%2FInterface_Counters%2F%ARG1%%2FInOut_bps&view=default-rrd-html',
				),
			),
		);
	}
        return true;
}

function SICEKIT_ParserFunctions_Monitoring_Magic(&$magicWords, $langCode) {
        // register our magic word
        $magicWords['monitoring'] = array(0, 'monitoring');
        return true;
}

function SICEKIT_ParserFunctions_Monitoring_RenderReplaceNames($format_string, $fqdn, $arg1, $arg2, $arg3, $arg4, $arg5) {
	$short = explode('.', $fqdn, 2);
	$short = htmlspecialchars($short[0]);
	$fqdn = htmlspecialchars($fqdn);
	$out = $format_string;
	$out = str_replace('%HOSTNAME%', $short, $out);
	$out = str_replace('%FQDN%', $fqdn, $out);
	$out = str_replace('%ARG1%', $arg1, $out);
	$out = str_replace('%ARG2%', $arg2, $out);
	$out = str_replace('%ARG3%', $arg3, $out);
	$out = str_replace('%ARG4%', $arg4, $out);
	$out = str_replace('%ARG5%', $arg5, $out);
	return $out;
}

function SICEKIT_ParserFunctions_Monitoring_Render(&$parser, $type, $maxcompat = 0, $fqdn = '', $arg1 = '', $arg2 = '', $arg3 = '', $arg4 = '', $arg5 = '') {
	global $SICEKIT_ParserFunctions_Monitoring_Config;
	if ($fqdn == '') {
		$fqdn = $parser->getTitle()->getText();
	}
	$out = '';
	if (!isset($SICEKIT_ParserFunctions_Monitoring_Config[$type])) {
		return array(sprintf("<b>monitoring: type %s is unknown.</b>", htmlspecialchars($type)), 'noparse' => true, 'isHTML' => true);
	}
	$format_string_maxcompat = '[%s %s] ';
	$format_string_html = '<a href="%s" class="external text sicekit_monitoringlink" title="%s for %s">%s</a> ';
	foreach($SICEKIT_ParserFunctions_Monitoring_Config[$type] as $system) {
		$url = SICEKIT_ParserFunctions_Monitoring_RenderReplaceNames($system['url'], $fqdn, $arg1, $arg2, $arg3, $arg4, $arg5);
		$desc = SICEKIT_ParserFunctions_Monitoring_RenderReplaceNames($system['desc'], $fqdn, $arg1, $arg2, $arg3, $arg4, $arg5);
		if ($maxcompat == 0) {
			$out .= sprintf($format_string_html, $url, $desc, $fqdn, $desc);
		} else {
			$out .= sprintf($format_string_maxcompat, $url, $desc);
		}
	}
	$out .= "\n";
	$opts = array($out);
	if ($maxcompat == 0) {
		$opts['noparse'] = true;
		$opts['isHTML'] = true;
	}
	return $opts;
}

