# idena-node-proxy log parser
A log parser for idena-node-proxy logs, creating validation statistics for administartors of shared/rented nodes.

[idena-node-proxy](https://github.com/idena-network/idena-node-proxy) is used to provide multiple different identities shared access to an [idena](https://idena.io) Proof-of-Person blockchain [node](https://github.com/idena-network/idena-go).

This script parses the log file created on the idena-node-proxy during an idena validation ceremony.

## Caveats

* This script was created to work with a shared node set up with my [Idena shared node guide](https://github.com/pocoloko/idena-shared-node-guide) and may not work with your setup.
* I am assuming idena-node-proxy log files are written to a file using the ```"logs": { "output": "file",``` option in the config.json file as described in [step 3 of my guide](https://github.com/pocoloko/idena-shared-node-guide#step-3-install-idena-node-proxy). If you are writing logs to ```stdout``` its up to you to move them to an appropriate file to be able to use the instructions for this log parser.
* The log parser uses the dna_identity entries from the log file, meaning it will include anyone that connected to your node on the day of the validation whether they actually validated on your node or not. The actual validation results are retrieved from the idena API using the identity that connected to your node, meaning that if the identity only connected to your node but in the end switched to a different node for verification, they will still be included in the statistics.

## Instructions

The script is not fully automated and requires some manual actions performed before the data is actually analized:

1. ```cd idena-node-proxy``` (wherever it may be)
