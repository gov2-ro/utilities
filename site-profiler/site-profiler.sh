#!/bin/bash

# original source:  https://www.baeldung.com/linux/check-website-availablilty

# set -x # uncomment for verbose / debug mode

trap "exit 1" TERM
export TOP_PID=$$
STDOUTFILE=".tempCurlStdOut" # temp file to store stdout
> $STDOUTFILE # cleans the file content

# Argument parsing follows our specification
for i in "$@"; do
  case $i in
    -f=*|--inputFile=*) # Specify input file containing a list of domains
      INPUTFILE="${i#*=}"
      shift
      ;;
    -o=*|--outputFile=*) # Specify the output CSV file
      OUTPUTFILE="${i#*=}"
      shift
      ;;
    -s|--silent)
      SILENT=true
      shift
      ;;
    *)
      >&2 echo "Unknown option: $i" # stderr
      exit 1
      ;;
  esac
done

if test -z "$INPUTFILE" || test -z "$OUTPUTFILE"; then
  >&2 echo "Missing required input or output file options" # stderr
  exit 1
fi

function stdOutput { 
  if ! test "$SILENT" = true; then
    echo "$1"
  fi
}

# Loop through the list of domains from the input file
while IFS= read -r DOMAIN; do
  stdOutput "Checking $DOMAIN"

  # if ping -q -w 1 -c 1 8.8.8.8 > /dev/null 2>&1; then
  # if ping -q -w 1 -c 1 1.1.1.1 > /dev/null 2>&1; then
  if true; then # if ping fails
    stdOutput "Internet connectivity OK"
    HTTPCODE=$(curl --max-time 5 -L --silent --write-out %{response_code} --output "$STDOUTFILE" "$DOMAIN")
    
    FINAL_URL=$(curl -s -o /dev/null -w %{url_effective} "$DOMAIN")
    CONTENT=$(<$STDOUTFILE)

    if test $HTTPCODE -eq 200; then
      stdOutput "HTTP STATUS CODE $HTTPCODE -> OK"
      STATUS="OK"
    else
      STATUS="Error: HTTP STATUS CODE $HTTPCODE"
    fi

    # You can add more checks here as needed

    # Store the results in the output CSV file
    echo "$DOMAIN,$FINAL_URL,$STATUS" >> "$OUTPUTFILE"
  else
    stdOutput "Internet connectivity not available"
    STATUS="No Internet"
    # Store the results in the output CSV file
    echo "$DOMAIN,, $STATUS" >> "$OUTPUTFILE"
  fi
done < "$INPUTFILE"
