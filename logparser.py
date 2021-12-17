#! /usr/bin/python3

# source and important instructions: https://github.com/pocoloko/idena-node-proxy-logparser
# A log parser for idena-node-proxy logs, creating validation statistics for administartors of shared/rented nodes.

import configparser # external config file loading
import os, logging # disk and logging stuff
import sys # for command line arguments
import json # JSON stuff
import requests # web stuff
import collections # used for counting number of idena states performed via node
from tqdm import tqdm # nice and easy progress bar for when querying API for identities

#Set up basic logging to file
logging.basicConfig(filename = ('logparser.log'), level=logging.DEBUG, format=' %(asctime)s -  %(levelname)s -  %(message)s')

# Initial setup of configuration.
def setup():
    ##### CONFIGURATION ##### use config.ini for edits, edit the path to file below as needed
    config_file = 'logparser.ini' # The configuration file, edit this if your config file is not in folder you are running the script from!

    # If we have a config file, load it. Note this doesn't necessarily mean that the config file is valid, just that it exists
    if os.path.exists(config_file) and os.path.getsize(config_file) > 0:
        config = configparser.ConfigParser(interpolation=None) # this is not ideal but disabling interpolation due to having % in URLs
        config.read(config_file) # Lets read our config file
    else: # If we don't have a config file, stop execution
        logging.error(f"A config file is required, we didn't find a config file where expected: {config_file}")
        raise SystemExit # Stops execution, throws an exception
    return config

# https://www.pythontutorial.net/python-basics/python-read-text-file/
# Load text file from disk
def load_file (filename):
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        with open(filename, 'r') as f:
            loaded = f.read().splitlines() # using this instead of just readlines() because readlines() returns \n as part of string
            logging.info(f"Loaded file to parse from disk, we have {str(len(loaded))} log file entries")
    else:
        logging.info('File not found')
        loaded = ""
    return loaded

# Save text to file
def save_file (filename, text):
    with open(filename,'w') as f:
        f.write(text)
        logging.info('We wrote string to file: '+ filename)

# return a tuple with (apikey, identity)
# skip if we get a "list index out of range" exception which indicates a log entry that isn't correct
# This is probably not the ideal way of dealing with this, but should work.
def process_entry (the_entry):
    jsonized = json.loads(the_entry[4])
    try:
        processed_entry = (the_entry[1], ( (jsonized["params"])[0]) )
    except IndexError as e: 
        logging.warning(f"Skipping potentially improper entry from log file: "+str(the_entry))
        return
    return processed_entry

# Return a list of tuples each containing one apikey and identity from the logfile
def process_log (entries):
    good_entries = []
    bad_entries = []
    for entry in entries:
        items = entry.split(" - ")
        if items[2] != '200':
            process = process_entry(items)
            if process != None: 
                bad_entries.append(process)
        else:
            process = process_entry(items)
            if process != None: 
                good_entries.append(process)
    logging.info(f"Processed log, we have {str(len(good_entries))} good entries and {str(len(bad_entries))} bad entries in our log file.")
    return good_entries, bad_entries

# Returns 2 lists of strings representing the IDs and the apikeysfrom this processing
def identities(good_entries):
    processed_ids = []
    processed_keys = []
    for entry in good_entries:
        processed_ids.append(f"{str(entry[1])}")
        processed_keys.append(f"{str(entry[0])}")
    return processed_ids, processed_keys

# Return number of IDs that are found in both current and previous validation logs
def number_repeats(current, previous):
    # convert string of IDs to sets
    current_set = set(current)
    previous_set = set(previous)
    result_set = current_set.intersection(previous_set) #use handy set function to compare
    return (str(len(result_set)))

# Ask the idena API for each identity and return a list of identities and their previous and current idena state
def query_identities (the_identities, the_epoch):
    the_validation = []
    the_states = []
    with tqdm(the_identities) as progress_bar: # nice progress bar to see where we are with the queries
        for identity in the_identities:
            url = f"https://api.idena.io/api/Epoch/{the_epoch}/Identity/{identity[1]}"
            res = requests.get(url)
            res.raise_for_status()
            progress_bar.update(1) # update progress bar
            # For some reason we have identities that do not exist in a given epoch in our logs, so we'll ignore those. 
            # Possibly someone created an identity after validation was finished or is connecting for a future validation
            try:
                the_validation.append( ( (identity[1]), (res.json()['result']['prevState']), (res.json()['result']['state']) ) )
                the_states.append( [ ( (res.json()['result']['prevState']), (res.json()['result']['state']) ) ] )
            except KeyError:
                logging.error(f"ERROR> Identity {identity[1]} in logfile does not exist in epoch {the_epoch}")
    return the_validation, the_states

# Separate successful and unsuccessful validations and count how many of each state change
def count_states (the_states):
    passed = {}
    failed = {}
    counted = collections.defaultdict(int)
    for state in the_states:
        counted[state[0]] += 1
    for count in counted:
        if ( count[1]) == "Undefined" or count[1] == "Zombie" or count[1] == "Suspended":
            failed[count] = counted[count]
        else:
            passed[count] = counted[count]
    counted_passed = dict(sorted(passed.items(), key=lambda item: item[1], reverse=True)) # sorted() returns a list of tuples hence dict() so we can process it later
    counted_failed = dict(sorted(failed.items(), key=lambda item: item[1], reverse=True)) # sorted() returns a list of tuples hence dict() so we can process it later
    return counted_passed, counted_failed

# Format the states nicely for later output
def format_states (states_passed, states_failed, the_epoch, number_good, number_bad, repeat_customers):
    clean_states = (f"Rental node statistics for epoch {the_epoch}\nAccepted API keys: {str(number_good)}\nRejected API keys: {str(number_bad)}\nRepeat customers from previous validation: {str(repeat_customers)}\n\n* Idena identities which passed validation:\n")
    for counted_state in states_passed:
        clean_states += (f"{counted_state[0]} -> {counted_state[1]} : {states_passed[counted_state]}\n")
    clean_states += (f"\n* Idena identities which failed validation:\n")
    for counted_state in states_failed:
        clean_states += (f"{counted_state[0]} -> {counted_state[1]} : {states_failed[counted_state]}\n")
    return clean_states

def main(config):
    if not (config['DEFAULT'].getboolean('LOGGING')):
        logging.disable(logging.CRITICAL) # disables all logging
    logging.info('--------------------------------START--------------------------------')
    if len(sys.argv) <= 2:
        logging.info('Missing command line arguments! quitting...')
        print('USAGE: ./logparser.py logfile.log epoch')
        print('for example: ./logparser dna_identity.epoch.74.unique.log 74')
        exit(1)

    parsefile = sys.argv[1] # TODO switch to argparse module and add more options and help and validation https://www.geeksforgeeks.org/command-line-arguments-in-python/
    epoch = sys.argv[2]

    previous_epoch = (str(int(epoch)-1))
    print('Parsing log file...')
    good_log, bad_log = process_log(load_file(parsefile))
    current_ids, current_keys = identities(good_log)
    save_file(f"{epoch}_ids_good.txt",("\n".join(current_ids)+"\n"))
    save_file(f"{epoch}_keys_good.txt",("\n".join(current_keys)+"\n"))

    # If we have a file for a previous epoch then we'll check number of repeat customers
    previous_ids = load_file(f"{previous_epoch}_ids_good.txt")
    if previous_ids != "":
        repeats = number_repeats(current_ids, previous_ids)
    else:
        repeats = "0"
    print('Querying API for identities (this may take a long time)...')
    validation_results, states = query_identities(good_log, epoch)
    ids_passed, ids_failed = count_states(states)
    print('Formatting data...')
    formatted_states = format_states(ids_passed, ids_failed, epoch, len(good_log), len(bad_log), repeats)
    save_file(f"{epoch}_log.txt",formatted_states)
    print(f"Done! Statistics saved to file: {epoch}_log.txt")

    logging.info('--------------------------------STOP--------------------------------')

if __name__ == "__main__":
    main(setup()) # Call main with the configuration as parameter, which is loaded via setup()
