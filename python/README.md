Executing the file:

$ python rest_app.py  (edit the BASEURL according to the controller ip (address, port))

Steps to follow to test the code:

1.
    Launch the mininet topology:
    $ sudo mn --controller=remote,ip=<ctrl>,port=<of_port> --topo=linear,3
    
    h1 (10.0.0.1) <------> s1 <---------> s2 <----------> s3 <--------> h3 (10.0.0.3)
                                           |------> h2 (10.0.0.2)
2.
    From the mininet terminal launch the xterm
    mn> xterm h1 h3
    
    2a. Test TCP traffic is allowed:
            h1 host:
               $ nc -l 9000 (tcp server)
            h3 host:
               $ nc 10.0.0.1 9000 (tcp client, type your message. It should appear in the
                                                                         h1 host terminal).
               
    2b. Test UDP traffic is getting dropped:
            h1 host:
               $ nc -lu 9000 (udp server)
            h3 host:
               $ nc -u 10.0.0.1 9000 (udp client, type your message. It shouldn't appear 
                                                                  in the h1 host terminal).           
    
Test cases:

      1. Launch the application after the switch <--> controller connection establishment.
      
      2. Launch the applicatoin before the switch <--> controller connection establishment.
