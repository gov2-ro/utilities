<?php
// Function to check if a domain is available using Technique #1
function isDomainAvailableTechnique1($domain)
{
    // Check if a valid URL is provided
    if (!filter_var($domain, FILTER_VALIDATE_URL)) {
        return false;
    }

    // Initialize cURL
    $curlInit = curl_init($domain);
    curl_setopt($curlInit, CURLOPT_CONNECTTIMEOUT, 10);
    curl_setopt($curlInit, CURLOPT_HEADER, true);
    curl_setopt($curlInit, CURLOPT_NOBODY, true);
    curl_setopt($curlInit, CURLOPT_RETURNTRANSFER, true);

    // Get the response
    $response = curl_exec($curlInit);
    curl_close($curlInit);

    if ($response) return true;

    return false;
}

// Function to check if a domain is available using Technique #2
function isDomainAvailableTechnique2($domain)
{
    $agent = "Mozilla/4.0 (compatible; MSIE 5.01; Windows NT 5.0)";
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $domain);
    curl_setopt($ch, CURLOPT_USERAGENT, $agent);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($ch, CURLOPT_VERBOSE, false);
    curl_setopt($ch, CURLOPT_TIMEOUT, 5);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, FALSE);
    curl_setopt($ch, CURLOPT_SSLVERSION, 3);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, FALSE);
    $page = curl_exec($ch);
    $httpcode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    if ($httpcode >= 200 && $httpcode < 300) return true;
    else return false;
}

// Function to check if a domain is available using Technique #3
function isDomainAvailableTechnique3($domain)
{
    ini_set("default_socket_timeout", "5");
    set_time_limit(5);
    $f = @fopen($domain, "r");
    if ($f) {
        $r = fread($f, 1000);
        fclose($f);
        if (strlen($r) > 1) {
            return true;
        }
    }
    return false;
}

// Function to process a list of domains
function processDomains($file, $outputFile)
{
    $lines = file($file, FILE_IGNORE_NEW_LINES);

    if ($lines === false) {
        die("Unable to read the file.");
    }

    $results = array();
    $header = ['Domain', 'Technique1', 'Technique2', 'Technique3'];

    // Open the CSV file for writing
    $csvFile = fopen($outputFile, 'w');
    if ($csvFile === false) {
        die("Unable to open the CSV file for writing.");
    }

    // Write the CSV header
    fputcsv($csvFile, $header);

    foreach ($lines as $line) {
        $domain = trim($line);
        $result = array(
            'Technique1' => isDomainAvailableTechnique1($domain),
            'Technique2' => isDomainAvailableTechnique2($domain),
            'Technique3' => isDomainAvailableTechnique3($domain),
        );

        $results[$domain] = $result;

        // Output the results to the console
        echo "Domain: $domain\n";
        echo "Technique #1: " . ($result['Technique1'] ? 'Up' : 'Down') . "\n";
        echo "Technique #2: " . ($result['Technique2'] ? 'Up' : 'Down') . "\n";
        echo "Technique #3: " . ($result['Technique3'] ? 'Online' : 'Offline') . "\n";
        echo "\n";

        // Append the results to the CSV file
        fputcsv($csvFile, array_merge([$domain], $result));
    }

    // Close the CSV file
    fclose($csvFile);

    return $results;
}

// Input file containing the list of domains
$inputFile = 'domainlist-institutii-publice-protocol.csv';

// Output file for the CSV
$outputFile = 'results.csv';

// Process domains and store results
$results = processDomains($inputFile, $outputFile);

// Output a message indicating the CSV file has been created
echo "Results have been saved to $outputFile.\n";
?>
