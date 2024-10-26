# dns_template_H8
bind9 template script


# Nsupdate on macbook

1. Create a File for Your TSIG Key on your macbook e.g., ~/dns-key.conf
2. Paste the key (/etc/bind/rndc.key) from the DNS server into it the file on your macbook
3. Now run this to test (Make sure to edit values before running)

Add PTR record:
```bash
nsupdate -k dns-key.conf << EOF
server test01.redrum.gg
zone 1.168.192.in-addr.arpa
update add 67.1.168.192.in-addr.arpa. 86400 PTR bing-prod.hhandler.redrum.gg.
send
EOF
```

Delete PTR record
```bash
nsupdate -k dns-key.conf << EOF
server test01.redrum.gg
zone 1.168.192.in-addr.arpa
delete 67.1.168.192.in-addr.arpa. 86400 PTR bing-prod.hhandler.redrum.gg.
send
EOF
```

# Database script 

The customerId from the hostconfig.cfg file need to be unik because I have no other way to control the different customers
So let's say hestehandler has 3 env. test, stage and prod then you need seprate customerId like 4000 for test, 4001 for stage and 4002 for prod. It's the only way I can control the "Hosts:" to the different env. If you need to add a ekstra host to the env. just add the entry in the config and run the script agian. If the hostName allready existe the script will not add it "Host 'cplane01-test' already exists in the database."

