<?php
/*
 This file is part of SICEKIT, http://oss.inqnet.at/trac/sicekit.
 SICEKIT CSS Extension
 Copyright (c) 2009 SICEKIT Development Team.
*/

if (!defined('MEDIAWIKI')) {
        die(-1);
}

//Avoid unstubbing $wgParser on setHook() too early on modern (1.12+) MW versions, as per r35980
if (defined('MW_SUPPORTS_PARSERFIRSTCALLINIT')) {
        $wgHooks['ParserFirstCallInit'][] = 'SICEKIT_ParserFunctions_ContractRef_Setup';
} else { // Otherwise do things the old fashioned way
        $wgExtensionFunctions[] = 'SICEKIT_ParserFunctions_ContractRef_Setup';
}

$wgHooks['LanguageGetMagic'][] = 'SICEKIT_ParserFunctions_ContractRef_Magic';

function SICEKIT_ParserFunctions_ContractRef_Setup() {
        global $wgParser;
        $wgParser->setFunctionHook('contractref', 'SICEKIT_ParserFunctions_ContractRef_Render');
        return true;
}

function SICEKIT_ParserFunctions_ContractRef_Magic(&$magicWords, $langCode) {
        // register our magic word
        $magicWords['contractref'] = array(0, 'contractref');
        return true;
}

function SICEKIT_ParserFunctions_ContractRef_Render(&$parser, $param1 = '') {
        // Nothing exciting here, just escape the user-provided
        // input and throw it back out again
        $contract = $param1;
        $contract_title = Title::newFromText($contract);
        if ($contract_title == NULL) return $contract;
        $contract_article = new Article($contract_title, 0);
        $contract_article->loadContent();
        $contract_content = $contract_article->getContent();
        $lines = split("\n", $contract_content);

        $data = array();
        $data['contract'] = '[[' . $contract. ']]';
        foreach($lines as $line) {
                if (strpos($line, "|COMPANYB=") === 0) {
                        $tmp = split("=", $line);
                        $data['companyb'] = '[[' . $tmp[1] . ']]';
                }
                if (strpos($line, "|STARTDATE=") === 0) {
                        $tmp = split("=", $line);
                        $data['date'] = $tmp[1];
                }
                if (strpos($line, "|NUMBERS=") === 0) {
                        $tmp = split("=", $line);
                        $data['numbers'] = $tmp[1];
                }
        }
        $string = implode(", ", $data);
        return $string;
}

