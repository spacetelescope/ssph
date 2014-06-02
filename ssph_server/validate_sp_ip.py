import os

def validate_ip() :

    # checking that the client is in the network range that we expect
    # to serve
    remote_addr = os.environ["REMOTE_ADDR"] 

    ### write your own if statements here
    if not remote_addr.startswith("130.167.") :
        return False
    if int(remote_addr.split(".")[2]) < 128 :
        return False
    ###

    return True
