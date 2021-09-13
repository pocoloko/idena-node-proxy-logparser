# idena-node-proxy log parser
A log parser for idena-node-proxy logs, creating validation statistics for administartors of shared/rented nodes.

[idena-node-proxy](https://github.com/idena-network/idena-node-proxy) is used to provide multiple different identities shared access to an [idena](https://idena.io) Proof-of-Person blockchain [node](https://github.com/idena-network/idena-go).

This script parses the log file created on the idena-node-proxy during an idena validation ceremony.

## Caveats

* This script was created to work with a shared node set up using my [Idena shared node guide](https://github.com/pocoloko/idena-shared-node-guide) and may not work with your setup, but probably will provided you have the correct log files.
* I am assuming idena-node-proxy log files are written to a file using the ```"logs": { "output": "file",``` option in the config.json file as described in [step 3 of my guide](https://github.com/pocoloko/idena-shared-node-guide#step-3-install-idena-node-proxy). If you are writing logs to ```stdout``` its up to you to extract them to an appropriate file to be able to use the instructions for this log parser.
* The log parser uses the dna_identity entries from the log file on the day of validation, meaning it will include anyone that connected to your node whether they actually validated on your node or not. The actual validation results are retrieved from the idena API using the identity that connected to your node, meaning that if the identity only connected to your node once but in the end switched to a different node for validation, they will still be included in the statistics. You should also make sure that the API keys from previous validations are removed from your idena-node-proxy before validation day.

## Full instructions

The script is not fully automated and requires some manual actions performed before the data is actually analized. **Ideally, this is done immediately after concensus on validation has been reached**

1. Complete the Script Usage first
2. Change directory to wherever your access.log file from idena-node-proxy is located: ```cd idena-node-proxy```
3. Extract only the log entries for the date of the validation: ```cat access.log | grep 2021-09-21 > validation.epoch.74.log```
4. This file now contains all the logs, but we only want the dna_identity entries: ```cat validation.epoch.74.log | grep dna_identity > dna_identity.epoch.74.log```
5. Now, because dna_identity endpoint is accessed many times by every identity, we need to remove all duplicates: ```awk '!a[$3]++' dna_identity.epoch.74.log > dna_identity.epoch.74.unique.log```
6. We now have the file we will actually process with the log parser script, so: ```./logparser.py dna_identity.epoch.74.unique.log```

## Script Usage

1. clone this repo
2. make sure you have the [requests python library](https://docs.python-requests.org/en/master/) installed
3. rename `logparser.ini_default` to `logparser.ini`. You do not need to edit anything in this version of the script.
4. Follow the Full Instructions
