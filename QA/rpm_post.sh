CACHEDIR=/var/cache/pycopia

id tester || (useradd -c Tester -G users,floppy -m tester ;
          (echo "tester" | passwd --stdin tester);
          printf "Remember to change new users (tester) password.\n" ;
	  )

if [ ! -d $CACHEDIR ] ; then
	mkdir -p $CACHEDIR
	chown tester:tester $CACHEDIR
	chmod 0770 $CACHEDIR
fi

if [ ! -f /etc/pycopia/Pyro.conf ] ; then
	cp /etc/pycopia/Pyro.conf.dist /etc/pycopia/Pyro.conf
fi

# ports defined in /etc/pycopia/Pyro.conf
if [ -f /etc/vmware-release ] && grep -q ESX /etc/vmware-release ; then
	esxcfg-firewall -o 9090,tcp,out,pyronstcp
	esxcfg-firewall -o 9090,udp,out,pyronsudp
	esxcfg-firewall -o 7766,tcp,in,agent
elif /etc/init.d/iptables status >/dev/null ; then
	iptables -A INPUT -p tcp -m tcp --dport 7766 -j ACCEPT
	iptables -A OUTPUT -p tcp -m tcp --dport 9090 -j ACCEPT
	iptables -A OUTPUT -p udp -m udp --dport 9090 -j ACCEPT
	/etc/init.d/iptables save
fi

