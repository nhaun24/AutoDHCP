# AutoDHCP
Python which writes DHCPD.CONF file from a CSV file

Install and Use:
Python3.10 (https://www.python.org/downloads/windows/) !!!!! Python3.10 Must add to path && Must disable path length limit  !!!!!
Run AutoDHCP.pyw (can make shortcut and add .ico file, but it does run without it)


CSV file can have any information you would like in it, although it must have the following collumns labeled as they are in the example
[VLAN ID, Purpose, Description, Location/ Shelf, CGN Space] OPTIONAL: Domain
    VLAN ID: Used for error index
    Purpose: Used to determine if config should be written for line (config only written if Purpose = "Data" or "Voice")
    Description: Used to name pools
    Location / Shelf: Also used to name pools
    CGN Space: Definition of DHCP Space
    Domain: Definition of Domain name
I have had some trouble with CSV's over 100 lines, and am still working on that

INPUT DOMAIN NAME : If "Use CSV" is chosen, but no collumn is defined in CSV for domain name, program will use "default.domain"
CUSTOM DNS SERVERS: unless otherwise specified in this field, program will use "8.8.8.8" and "8.8.4.4"
CUSTOM LEASE TIME : unless otherwise specified in this field, program will use "86400"


By default, this program starts the DHCP pools at the fourth available IP in the block if this needs to be changed, you may change the following:
    start_ip, end_ip = str(ip_range[3]), str(ip_range[-1])

          str(ip_range[3]) = fourth IP available, this is indexed from 0 IE: 0=.2, 1=.3, 2=.4, 3=.5 ETC...
