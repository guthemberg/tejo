=================
Short description
=================

These scripts inject faults in FreeBSD systems running MongoDB.

=================
How to run
=================

/bin/sh script_name.sh DURATION INTENSITY

For running a script, we need to define its DURATION in seconds and its 
INTENSITY, where intensity ranges from 0.1 to 1.0 (limited to steps of 
0.1, i.e. in sequence, .1, .2, .3, and so on)

=================
Details
=================

List of fault codes and very short descriptions:

Fault code	: Description	
0			: no fault

1			: downtime	of mongo db	

2			: Packet loss using dummynet

3			: latency with dummynet

4			: bandwidth with dummynet

Outputs are written on /tmp directory. See the code for further details.

Notable scripts:
  - inject_faults.sh runs a single fault campaign in a linux node
  - run_fault_campaigns.sh runs multiple fault campaigns in a freebsd box
