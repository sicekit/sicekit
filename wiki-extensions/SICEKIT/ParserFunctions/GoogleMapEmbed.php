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
        $wgHooks['ParserFirstCallInit'][] = 'SICEKIT_ParserFunctions_GoogleMapEmbed_Setup';
} else { // Otherwise do things the old fashioned way
        $wgExtensionFunctions[] = 'SICEKIT_ParserFunctions_GoogleMapEmbed_Setup';
}

$wgHooks['LanguageGetMagic'][] = 'SICEKIT_ParserFunctions_GoogleMapEmbed_LanguageGetMagic';
$wgHooks['ParserAfterTidy'][] = 'SICEKIT_ParserFunctions_GoogleMapEmbed_ParserAfterTidy';
$SICEKIT_ParserFunctions_GoogleMapEmbed_MarkerList = array();

function SICEKIT_ParserFunctions_GoogleMapEmbed_Setup() {
        global $wgParser;
        $wgParser->setFunctionHook('googlemapembed', 'SICEKIT_ParserFunctions_GoogleMapEmbed_Render');
        return true;
}

function SICEKIT_ParserFunctions_GoogleMapEmbed_LanguageGetMagic(&$magicWords, $langCode) {
        // register our magic word
        $magicWords['googlemapembed'] = array(0, 'googlemapembed');
        return true;
}

function SICEKIT_ParserFunctions_GoogleMapEmbed_Render(&$parser, $ll, $spn) {
	global $SICEKIT_ParserFunctions_GoogleMapEmbed_MarkerList;
	$ll = htmlspecialchars($ll);
	$spn = htmlspecialchars($spn);
	$string = '<iframe width="650" height="350" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" src="http://maps.google.com/maps?ie=UTF8&amp;ll=%LL%&amp;spn=%SPN%&amp;z=15&amp;output=embed"></iframe><br /><small><a href="http://maps.google.com/maps?ie=UTF8&amp;ll=%LL%&amp;spn=%SPN%&amp;z=15&amp;source=embed" style="color:#0000FF;text-align:left">View Larger Map</a></small>'."\n";
	$string = str_replace('%LL%', $ll, $string);
	$string = str_replace('%SPN%', $spn, $string);
	$current_marker_id = count(array_keys($SICEKIT_ParserFunctions_GoogleMapEmbed_MarkerList));
	$current_marker = "@@XX-SICEKIT_ParserFunctions_GoogleMapEmbed_Marker-$current_marker_id-XX@@";
	$SICEKIT_ParserFunctions_GoogleMapEmbed_MarkerList[$current_marker] = $string;
        return $current_marker;
}

function SICEKIT_ParserFunctions_GoogleMapEmbed_ParserAfterTidy(&$parser, &$text) {
	global $SICEKIT_ParserFunctions_GoogleMapEmbed_MarkerList;
	// replace markers with actual output
	$text = str_replace(array_keys($SICEKIT_ParserFunctions_GoogleMapEmbed_MarkerList), array_values($SICEKIT_ParserFunctions_GoogleMapEmbed_MarkerList), $text);
	return true;
}

