<?php

# Define a setup function
$wgExtensionFunctions[] = 'efContractRef_Setup';
# Add a hook to initialise the magic word
$wgHooks['LanguageGetMagic'][]       = 'efContractRef_Magic';

function efContractRef_Setup() {
        global $wgParser;
        $wgParser->setFunctionHook( 'contractref', 'efContractRefRender' );
        return true;
}

function efContractRef_Magic(&$magicWords, $langCode) {
        $magicWords['contractref'] = array(0,'contractref');
        return true;
}

function efContractRefRender( &$parser, $param1 = '' ) {
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

