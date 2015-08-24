import requests
from requests.auth import HTTPBasicAuth
from websocket import create_connection

"""
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


"""

BASEURL = 'http://192.168.56.10:8181/restconf/'

def createDataChangeListener():

    # url for requesting the stream
    url = BASEURL + 'operations/sal-remote:create-data-change-event-subscription'

    # set the content type to json, we would like to process the json data
    headers = { 'content-type' : 'application/xml',
                'accept'       : 'application/json' }

    # body of the request message
    payload = '<input xmlns="urn:opendaylight:params:xml:ns:yang:controller:md:sal:remote"> \
               <path xmlns:a="urn:TBD:params:xml:ns:yang:network-topology">/a:network-topology</path> \
               <datastore xmlns="urn:sal:restconf:event:subscription">OPERATIONAL</datastore> \
               <scope xmlns="urn:sal:restconf:event:subscription">SUBTREE</scope> \
           </input>'

    responseData = requests.post( url, data=payload,
                                  headers= headers,
                                  auth= HTTPBasicAuth('admin', 'admin'))
    streamName = responseData.text

    if ('error' in streamName):
        print 'Error: ' + streamName
        return

    streamName = responseData.json()
    return streamName['output'] ['stream-name']


def subscribeStream(streamName):

    url = BASEURL + 'streams/stream/' + streamName

    # set the content type to json, we would like to process the json data
    headers = { 'content-type' : 'application/json',
                'accept'       : 'application/json' }

    responseData = requests.get(url, headers= headers, auth= HTTPBasicAuth('admin', 'admin'))
    return responseData.headers[ 'location' ]

def listenStream(ws):

    while True:
        result = ws.recv()
        #print "change === "
        #print result
        printDevice(getNetworkTopology())

    ws.close()

def getNetworkTopology():

    # set the url to read the network topology
    url = BASEURL + 'operational/network-topology:network-topology'

    # set the content type to json, we would like to process the json data
    headers = { 'content-type' : 'application/json',
                'accept'       : 'application/json' }

    # set the request to the controller and collect the
    # topology json.

    responseData = requests.get(url, headers= headers, auth= HTTPBasicAuth( 'admin', 'admin'))
    topoInfo = responseData.json()
    return topoInfo

def printDevice(topo):

    print '== topology =='
    #print topo

    if ('network-topology' in topo):
        network = topo['network-topology'] ['topology']

        for nodes in network:
            print '== node =='
            if nodes.get('node') != None :
                for node in nodes['node']:
                    #print node
                    print node['node-id']
                    install_flow(node['node-id'])

def install_flow(dpid):
    """
    This will install the flow to the switch
    :param dpid: dpid of the OF switch
    :return:
    """

    flow_url = BASEURL + 'config/opendaylight-inventory:nodes/node/' + dpid + '/table/0/flow/'

    # set the content type to json, we would like to process the json data
    headers = { 'content-type' : 'application/json',
                'accept'       : 'application/json' }

    # flow configuration responsible for allowing all the traffic.
    flow_id_allow_all = 100
    flow_priority_allow_all = 100
    flow_url_allow_all = flow_url + str(flow_id_allow_all)
    payload_allow_all = get_payload_allow_all(flow_id_allow_all, flow_priority_allow_all)

    responseData = requests.put( flow_url_allow_all, data=payload_allow_all,
                                  headers= headers,
                                  auth= HTTPBasicAuth('admin', 'admin'))

    print responseData

    # prepare flow to to drop all the udp packets.
    flow_id_udp_drop = 200
    flow_priority_udp_drop = 200
    flow_url_udp_drop = flow_url + str(flow_id_udp_drop)
    payload_drop_udp = get_payload_udp_drop(flow_id_udp_drop, flow_priority_udp_drop)

    responseData = requests.put( flow_url_udp_drop, data=payload_drop_udp,
                                  headers= headers,
                                  auth= HTTPBasicAuth('admin', 'admin'))

    print responseData

def get_payload_udp_drop(flowid, flow_priority) :
    """
    create the payload for the udp_drop.
    :param flowid: flow id
    :return: payload for the request
    """

    return '{\
                    "flow": {\
                        "match": {\
                            "ethernet-match": {\
                                    "ethernet-type": {\
                                        "type": "2048"\
                                    }\
                            },\
                            "ip-match": {\
                                "ip-protocol": "17"\
                            }\
                        },\
                    "table_id": "0",\
                    "id":' + str(flowid) +','+\
                    '"cookie_mask": "10",\
                    "installHw": "false",\
                    "hard-timeout": "0",\
                    "cookie": "10",\
                    "idle-timeout": "0",\
                    "flow-name": "DropFlow",\
                    "priority":' + str(flow_priority) + ',\
                    "barrier": "false"\
                    }\
                }'

def get_payload_allow_all(flowid, flow_priority) :
    """
    create the payload for the allow all traffic (arp, tcp etc.).
    :param flowid: flow id
    :return: payload for the request
    """

    return '{\
                    "flow": {\
                          "instructions": {\
                            "instruction": {\
                                    "order": "0",\
                                    "apply-actions": {\
                                        "action": {\
                                            "order": "0",\
                                            "output-action": {\
                                                "output-node-connector": "NORMAL"\
                                            }\
                                        }\
                                    }\
                            }\
                          },\
                    "table_id": "0",\
                    "id":' + str(flowid) +','+\
                    '"cookie_mask": "10",\
                    "installHw": "false",\
                    "hard-timeout": "0",\
                    "cookie": "10",\
                    "idle-timeout": "0",\
                    "flow-name": "FloodFlow",\
                    "priority":' + str(flow_priority) + ',\
                    "barrier": "false"\
                    }\
                }'

def main():
    printDevice(getNetworkTopology())
    streamName = createDataChangeListener()
    print streamName

    streamUrl = subscribeStream(streamName)

    streamUrl = streamUrl.replace('http:', 'ws:', 1 )
    ws = create_connection(streamUrl)

    listenStream(ws)



if __name__ == '__main__':
    main()