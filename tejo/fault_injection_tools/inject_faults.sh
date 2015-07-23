#!/bin/sh

RECOVERY_DELAY=60
FAULT_DURATION=900

for fault_type in 2 3 4 5
#for fault_type in 5
do
        for intensity in 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0
        do
                ts=`/bin/date`
                /bin/echo -n "[${ts}] injecting fault $fault_type with intensity of $intensity (fault dur. ${FAULT_DURATION} sec.)..."
                if [ $fault_type -eq 2 ]; then
                        /bin/tcsh -c "/bin/sh /home/user/tejo/tejo/fault_injection_tools/packet_loss_fault.sh $FAULT_DURATION $intensity >& /tmp/packet_loss_fault_${intensity}.log"
                        /bin/sleep $RECOVERY_DELAY
                elif [ $fault_type -eq 3 ]; then
                        /bin/tcsh -c "/bin/sh /home/user/tejo/tejo/fault_injection_tools/latency_fault.sh $FAULT_DURATION $intensity >& /tmp/latency_fault_${intensity}.log"
                        /bin/sleep $RECOVERY_DELAY
                elif [ $fault_type -eq 4 ]; then
                        /bin/tcsh -c "/bin/sh /home/user/tejo/tejo/fault_injection_tools/bandwidth_fault.sh $FAULT_DURATION $intensity >& /tmp/bandwidth_fault_${intensity}.log"
                        /bin/sleep $RECOVERY_DELAY
                elif [ $fault_type -eq 5 ]; then
                        /bin/tcsh -c "/bin/sh /home/user/tejo/tejo/fault_injection_tools/memory_fault.sh $FAULT_DURATION $intensity >& /tmp/memory_fault_${intensity}.log"
                        /bin/sleep $RECOVERY_DELAY
                        /bin/sleep $RECOVERY_DELAY
                        /bin/sleep $RECOVERY_DELAY
                        /bin/sleep $RECOVERY_DELAY
                        /bin/sleep $RECOVERY_DELAY
                else  
                        echo "nothing to do."  
                fi
                /bin/echo " done."
        done
        
done

/bin/echo "all done!"