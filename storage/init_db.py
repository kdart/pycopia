#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Place initial values in database.

"""

import sys
import os

from sqlalchemy import create_engine

from pycopia import aid
from pycopia import urlparse
from pycopia.db import models
from pycopia.db import tables
from pycopia.db import config

from pycopia.ISO import iso639a
from pycopia.ISO import iso3166

# schedules

def do_schedules(session):
    for name, m, h, dom, mon, dow in (
          ("Minutely", "*", "*", "*", "*", "*"),
          ("Hourly", "15", "*", "*", "*", "*"),
          ("Daily", "30", "4", "*", "*", "*"),
          ("TwiceADay", "40", "5,17", "*", "*", "*"),
          ("Weekly", "45", "4", "*", "*", "6"),
          ("BiWeekly", "45", "3", "*", "*", "3,6"),
          ("Monthly", "45", "5", "1", "*", "*"),
          ("Yearly", "55", "6", "1", "12", "*"),
          ):
        session.add(models.create(models.Schedule, name=name, minute=m, hour=h, day_of_month=dom, month=mon, day_of_week=dow))
    session.commit()


# functional areas of systems and corporate entities.
def do_functional_areas(session):
    for name, desc in (
            ("computing", "Basic computing, such as operating system."),
            ("UI", "Any user interface"),
            ("GUI", "Graphical user interface"),
            ("TUI", "Text user interface"),
            ("webUI", "Browser based user interface"),
            ("Documentation", "Documentation of something."),
            ("Networking", "Routing, bridging, etc."),
            ("telephony", "Telephony service."),
            ("datacom", "Data communications service"),
            ("repair", "Repair service"),
            ("cloud", "Cloud computing."),
            ("AAA", "Authentication, authorization, and accounting."),
            ("CA", "Certificate authority."),
            ):
        session.add(models.create(models.FunctionalArea, name=name, description=desc))
    session.commit()

def do_software_category(session):
    for name, desc in (
            ("OS", "An operating system."),
            ("spreadsheet", "A spreadsheet."),
            ("wordprocessor", "A wordprocessor."),
            ("texteditor", "A plain text editor."),
            ("proxy", "A type of network protocol proxy."),
            ("browser", "Can render web content."),
            ("webserver", "Serves web pages and content."),
            ("selenium", "A Selenium server."),
            ("mua", "A mail user agent (e.g. pine, thunderbird, or claws-mail)."),
            ("mta", "A Mail transfer agent or SMTP server (e.g. sendmail, courier)."),
            ("dnsserver", "Responds to DNS queries."),
            ("database", "A database server."),
            ("remoteshell", "Provides some remote command shell."),
            ("remotedesktop", "Provides a remote desktop."),
            ("dhcpserver", "Provides DHCP services."),
            ("tftpserver", "Provides TFTP server, usually for network booting."),
            ("cupsserver", "A CUPS printer server."),
            ("nfsserver", "An NFS server."),
            ("nfsclient", "An NFS client."),
            ("iscsiserver", "A iSCSI target (server)."),
            ("iscsi_initiator", "A iSCSI initiator (client)."),
            ("ntp", "Provides network time sync service."),
            ("ftpserver", "Provides an FTP server."),
            ("vixclient", "A VMware VIX client."),
            ("hypervisor", "A hypervisor (e.g. VMware ESX)."),
        ):
        session.add(models.create(models.SoftwareCategory, name=name, description=desc))
    session.commit()


def do_attribute_types(session):
    for name, vtype, desc in (
            ("isbase", 5, "Is a base item (don't follow fallback)."),
            ("fallback", 1, "Name of fallback item for more attributes, if any."),
            ("login", 1, "Username to access, if needed by accessmethod."),
            ("password",1, "Password for login, if needed by accessmethod."),
            ("accessmethod",1, 'Method of device access supported by Configurator constructor.'),
            ("initialaccessmethod",1, 'Initial access method to perform basic configure. e.g. "console"'),
            ("snmp_ro_community",1, "SNMP community string for RO access."),
            ("snmp_rw_community",1, "SNMP community string for RW access."),
            ("console_server",0, "Consoler server '(host, port)', if any."),
            ("power_controller",0, "Power controller '(name, socket)', if any."),
            ("monitor_port",0, "Etherswitch port that mirrors primary data interface."),
            ("admin_interface",1, "Name of administrative interface, if any."),
            ("data_interfaces",0, "Comma separated list of data/test interfaces."),
            ("phonenumber",1, "Assigned phone number, if a phone."),
            ("useragent", 1, "If a browser, the user agent."),
            ("wireless", 5, "Is a wireless communication device."),
            ("webenabled", 5, "Is a WWW enabled device."),
            ("url",1, "base URL to access device, if required."),
            ("serviceport", 1, "TCP/UDP/IP service port in the form 'tcp/80'."),
            ("servicepath", 1, "Path part of a URL pointing to service location."),
            ("serviceprotocol", 1, "Protocol part of a URL pointing to service location."),
            ("protocol", 1, "Internet protocol a software implements."),
            ("hostname", 1, "Name to use as host name. Overrides base name."),
            ("state", 1, "The current state of the device. Arbitrary string used by test framework."),
            ):
        session.add(models.create(models.AttributeType, name=name, value_type=vtype,
                description=desc))
        session.commit()

def do_env_attribute_types(session):
    for name, vtype, desc in (
            ("state", 1, "The current state of the environment. Test defined string."),
            ):
        session.add(models.create(models.EnvironmentAttributeType, name=name, value_type=vtype,
                description=desc))
        session.commit()

def do_language(session):
    for code, name in iso639a.LANGUAGECODES.items():
        session.add(models.create(models.Language, name=name.encode("utf-8"), isocode=code.strip()))
    session.commit()

def do_country(session):
    for code, name in iso3166.COUNTRYCODES.items():
          name = unicode(name, "ISO-8859-1").title()
          session.add(models.create(models.Country, name=name, isocode=code.strip()))
    session.commit()

def do_equipment_category(session):
    for name in (
           "other",
           "unknown",
           "chassis",
           "backplane",
           "container",     # chassis slot or daughter-card holder
           "powerSupply",
           "fan",
           "sensor",
           "module",        # plug-in card or daughter-card
           "port",
           "stack",        # stack of multiple chassis entities
           "cpu"):
        session.add(models.create(models.EquipmentCategory, name=name))
    session.commit()


def do_interface_types(session):
    for name, enumeration in (
            ("other", 1),          #  none of the following
            ("regular1822", 2),
            ("hdh1822", 3),
            ("ddnX25", 4),
            ("rfc877x25", 5),
            ("ethernetCsmacd", 6), #  for all ethernet-like interfaces, regardless of speed, as per RFC3635
            ("iso88024TokenBus", 8),
            ("iso88025TokenRing", 9),
            ("iso88026Man", 10),
            ("proteon10Mbit", 12),
            ("proteon80Mbit", 13),
            ("hyperchannel", 14),
            ("fddi", 15),
            ("lapb", 16),
            ("sdlc", 17),
            ("ds1", 18),            #  DS1-MIB
            ("propPointToPointSerial", 22), #  proprietary serial
            ("ppp", 23),
            ("softwareLoopback", 24),
            ("eon", 25),            #  CLNP over IP
            ("ethernet3Mbit", 26),
            ("nsip", 27),           #  XNS over IP
            ("slip", 28),           #  generic SLIP
            ("ultra", 29),          #  ULTRA technologies
            ("ds3", 30),            #  DS3-MIB
            ("sip", 31),            #  SMDS, coffee
            ("frameRelay", 32),     #  DTE only.
            ("rs232", 33),
            ("para", 34),           #  parallel-port
            ("arcnet", 35),         #  arcnet
            ("arcnetPlus", 36),     #  arcnet plus
            ("atm", 37),            #  ATM cells
            ("miox25", 38),
            ("sonet", 39),          #  SONET or SDH
            ("x25ple", 40),
            ("iso88022llc", 41),
            ("localTalk", 42),
            ("smdsDxi", 43),
            ("frameRelayService", 44),  #  FRNETSERV-MIB
            ("v35", 45),
            ("hssi", 46),
            ("hippi", 47),
            ("modem", 48),          #  Generic modem
            ("aal5", 49),           #  AAL5 over ATM
            ("sonetPath", 50),
            ("sonetVT", 51),
            ("smdsIcip", 52),       #  SMDS InterCarrier Interface
            ("propVirtual", 53),    #  proprietary virtual/internal
            ("propMultiplexor", 54),#  proprietary multiplexing
            ("ieee80212", 55),      #  100BaseVG
            ("fibreChannel", 56),   #  Fibre Channel
            ("hippiInterface", 57), #  HIPPI interfaces
            ("aflane8023", 59),     #  ATM Emulated LAN for 802.3
            ("aflane8025", 60),     #  ATM Emulated LAN for 802.5
            ("cctEmul", 61),        #  ATM Emulated circuit
            ("isdn", 63),           #  ISDN and X.25
            ("v11", 64),            #  CCITT V.11/X.21
            ("v36", 65),            #  CCITT V.36
            ("g703at64k", 66),      #  CCITT G703 at 64Kbps
            ("qllc", 68),           #  SNA QLLC
            ("channel", 70),        #  channel
            ("ieee80211", 71),      #  radio spread spectrum
            ("ibm370parChan", 72),  #  IBM System 360/370 OEMI Channel
            ("escon", 73),          #  IBM Enterprise Systems Connection
            ("dlsw", 74),           #  Data Link Switching
            ("isdns", 75),          #  ISDN S/T interface
            ("isdnu", 76),          #  ISDN U interface
            ("lapd", 77),           #  Link Access Protocol D
            ("ipSwitch", 78),       #  IP Switching Objects
            ("rsrb", 79),           #  Remote Source Route Bridging
            ("atmLogical", 80),     #  ATM Logical Port
            ("ds0", 81),            #  Digital Signal Level 0
            ("ds0Bundle", 82),      #  group of ds0s on the same ds1
            ("bsc", 83),            #  Bisynchronous Protocol
            ("async", 84),          #  Asynchronous Protocol
            ("cnr", 85),            #  Combat Net Radio
            ("iso88025Dtr", 86),    #  ISO 802.5r DTR
            ("eplrs", 87),          #  Ext Pos Loc Report Sys
            ("arap", 88),           #  Appletalk Remote Access Protocol
            ("propCnls", 89),       #  Proprietary Connectionless Protocol
            ("hostPad", 90),        #  CCITT-ITU X.29 PAD Protocol
            ("termPad", 91),        #  CCITT-ITU X.3 PAD Facility
            ("frameRelayMPI", 92),  #  Multiproto Interconnect over FR
            ("x213", 93),           #  CCITT-ITU X213
            ("adsl", 94),           #  Asymmetric Digital Subscriber Loop
            ("radsl", 95),          #  Rate-Adapt. Digital Subscriber Loop
            ("sdsl", 96),           #  Symmetric Digital Subscriber Loop
            ("vdsl", 97),           #  Very H-Speed Digital Subscrib. Loop
            ("iso88025CRFPInt", 98), #  ISO 802.5 CRFP
            ("myrinet", 99),        #  Myricom Myrinet
            ("voiceEM", 100),       #  voice recEive and transMit
            ("voiceFXO", 101),      #  voice Foreign Exchange Office
            ("voiceFXS", 102),      #  voice Foreign Exchange Station
            ("voiceEncap", 103),    #  voice encapsulation
            ("voiceOverIp", 104),   #  voice over IP encapsulation
            ("atmDxi", 105),        #  ATM DXI
            ("atmFuni", 106),       #  ATM FUNI
            ("atmIma", 107),       #  ATM IMA
            ("pppMultilinkBundle", 108), #  PPP Multilink Bundle
            ("ipOverCdlc", 109),   #  IBM ipOverCdlc
            ("ipOverClaw", 110),   #  IBM Common Link Access to Workstn
            ("stackToStack", 111), #  IBM stackToStack
            ("virtualIpAddress", 112), #  IBM VIPA
            ("mpc", 113),          #  IBM multi-protocol channel support
            ("ipOverAtm", 114),    #  IBM ipOverAtm
            ("iso88025Fiber", 115), #  ISO 802.5j Fiber Token Ring
            ("tdlc", 116),         #  IBM twinaxial data link control
            ("hdlc", 118),         #  HDLC
            ("lapf", 119),         #  LAP F
            ("v37", 120),          #  V.37
            ("x25mlp", 121),       #  Multi-Link Protocol
            ("x25huntGroup", 122), #  X25 Hunt Group
            ("trasnpHdlc", 123),   #  Transp HDLC
            ("interleave", 124),   #  Interleave channel
            ("fast", 125),         #  Fast channel
            ("ip", 126),           #  IP (for APPN HPR in IP networks)
            ("docsCableMaclayer", 127),  #  CATV Mac Layer
            ("docsCableDownstream", 128), #  CATV Downstream interface
            ("docsCableUpstream", 129),  #  CATV Upstream interface
            ("a12MppSwitch", 130), #  Avalon Parallel Processor
            ("tunnel", 131),       #  Encapsulation interface
            ("coffee", 132),       #  coffee pot
            ("ces", 133),          #  Circuit Emulation Service
            ("atmSubInterface", 134), #  ATM Sub Interface
            ("l2vlan", 135),       #  Layer 2 Virtual LAN using 802.1Q
            ("l3ipvlan", 136),     #  Layer 3 Virtual LAN using IP
            ("l3ipxvlan", 137),    #  Layer 3 Virtual LAN using IPX
            ("digitalPowerline", 138), #  IP over Power Lines
            ("mediaMailOverIp", 139), #  Multimedia Mail over IP
            ("dtm", 140),        #  Dynamic syncronous Transfer Mode
            ("dcn", 141),    #  Data Communications Network
            ("ipForward", 142),    #  IP Forwarding Interface
            ("msdsl", 143),       #  Multi-rate Symmetric DSL
            ("ieee1394", 144), #  IEEE1394 High Performance Serial Bus
            ("if-gsn", 145),       #    HIPPI-6400
            ("dvbRccMacLayer", 146), #  DVB-RCC MAC Layer
            ("dvbRccDownstream", 147),  #  DVB-RCC Downstream Channel
            ("dvbRccUpstream", 148),  #  DVB-RCC Upstream Channel
            ("atmVirtual", 149),   #  ATM Virtual Interface
            ("mplsTunnel", 150),   #  MPLS Tunnel Virtual Interface
            ("srp", 151),   #  Spatial Reuse Protocol
            ("voiceOverAtm", 152),  #  Voice Over ATM
            ("voiceOverFrameRelay", 153),   #  Voice Over Frame Relay
            ("idsl", 154),      #  Digital Subscriber Loop over ISDN
            ("compositeLink", 155),  #  Avici Composite Link Interface
            ("ss7SigLink", 156),     #  SS7 Signaling Link
            ("propWirelessP2P", 157),  #   Prop. P2P wireless interface
            ("frForward", 158),    #  Frame Forward Interface
            ("rfc1483", 159),   #  Multiprotocol over ATM AAL5
            ("usb", 160),       #  USB Interface
            ("ieee8023adLag", 161),  #  IEEE 802.3ad Link Aggregate
            ("bgppolicyaccounting", 162), #  BGP Policy Accounting
            ("frf16MfrBundle", 163), #  FRF .16 Multilink Frame Relay
            ("h323Gatekeeper", 164), #  H323 Gatekeeper
            ("h323Proxy", 165), #  H323 Voice and Video Proxy
            ("mpls", 166), #  MPLS
            ("mfSigLink", 167), #  Multi-frequency signaling link
            ("hdsl2", 168), #  High Bit-Rate DSL - 2nd generation
            ("shdsl", 169), #  Multirate HDSL2
            ("ds1FDL", 170), #  Facility Data Link 4Kbps on a DS1
            ("pos", 171), #  Packet over SONET/SDH Interface
            ("dvbAsiIn", 172), #  DVB-ASI Input
            ("dvbAsiOut", 173), #  DVB-ASI Output
            ("plc", 174), #  Power Line Communtications
            ("nfas", 175), #  Non Facility Associated Signaling
            ("tr008", 176), #  TR008
            ("gr303RDT", 177), #  Remote Digital Terminal
            ("gr303IDT", 178), #  Integrated Digital Terminal
            ("isup", 179), #  ISUP
            ("propDocsWirelessMaclayer", 180), #  Cisco proprietary Maclayer
            ("propDocsWirelessDownstream", 181), #  Cisco proprietary Downstream
            ("propDocsWirelessUpstream", 182), #  Cisco proprietary Upstream
            ("hiperlan2", 183), #  HIPERLAN Type 2 Radio Interface
            ("sonetOverheadChannel", 185), #  SONET Overhead Channel
            ("digitalWrapperOverheadChannel", 186), #  Digital Wrapper
            ("aal2", 187), #  ATM adaptation layer 2
            ("radioMAC", 188), #  MAC layer over radio links
            ("atmRadio", 189), #  ATM over radio links
            ("imt", 190), #  Inter Machine Trunks
            ("mvl", 191), #  Multiple Virtual Lines DSL
            ("reachDSL", 192), #  Long Reach DSL
            ("frDlciEndPt", 193), #  Frame Relay DLCI End Point
            ("atmVciEndPt", 194), #  ATM VCI End Point
            ("opticalChannel", 195), #  Optical Channel
            ("opticalTransport", 196), #  Optical Transport
            ("propAtm", 197), #   Proprietary ATM
            ("voiceOverCable", 198), #  Voice Over Cable Interface
            ("infiniband", 199), #  Infiniband
            ("teLink", 200), #  TE Link
            ("q2931", 201), #  Q.2931
            ("virtualTg", 202), #  Virtual Trunk Group
            ("sipTg", 203), #  SIP Trunk Group
            ("sipSig", 204), #  SIP Signaling
            ("docsCableUpstreamChannel", 205), #  CATV Upstream Channel
            ("econet", 206), #  Acorn Econet
            ("pon155", 207), #  FSAN 155Mb Symetrical PON interface
            ("pon622", 208), #  FSAN622Mb Symetrical PON interface
            ("bridge", 209), #  Transparent bridge interface
            ("linegroup", 210), #  Interface common to multiple lines
            ("voiceEMFGD", 211), #  voice E&M Feature Group D
            ("voiceFGDEANA", 212), #  voice FGD Exchange Access North American
            ("voiceDID", 213), #  voice Direct Inward Dialing
            ("mpegTransport", 214), #  MPEG transport interface
            ("gtp", 216), #  GTP(GPRS Tunneling Protocol)
            ("pdnEtherLoop1", 217), #  Paradyne EtherLoop 1
            ("pdnEtherLoop2", 218), #  Paradyne EtherLoop 2
            ("opticalChannelGroup", 219), #  Optical Channel Group
            ("homepna", 220), #  HomePNA ITU-T G.989
            ("gfp", 221), #  Generic Framing Procedure(GFP)
            ("ciscoISLvlan", 222), #  Layer 2 Virtual LAN using Cisco ISL
            ("actelisMetaLOOP", 223), #  Acteleis proprietary MetaLOOP High Speed Link
            ("fcipLink", 224), #  FCIP Link
            ("rpr", 225), #  Resilient Packet Ring Interface Type
            ("qam", 226), #  RF Qam Interface
            ("lmp", 227), #  Link Management Protocol
            ("cblVectaStar", 228), #  Cambridge Broadband Networks Limited VectaStar
            ("docsCableMCmtsDownstream", 229), #  CATV Modular CMTS Downstream Interface
            ("macSecControlledIF", 231), #  MACSecControlled
            ("macSecUncontrolledIF", 232), #  MACSecUncontrolled
            ("aviciOpticalEther", 233), #  Avici Optical Ethernet Aggregate
            ("atmbond", 234), #  atmbond
            ("voiceFGDOS", 235), #  voice FGD Operator Services
            ("mocaVersion1", 236), #  MultiMedia over Coax Alliance(MoCA) Interface as documented in information provided privately to IANA
            ("ieee80216WMAN", 237), #  IEEE 802.16 WMAN interface
            ("adsl2plus", 238), #  Asymmetric Digital Subscriber Loop Version 2, Version 2 Plus and all variants
            ("dvbRcsMacLayer", 239), #  DVB-RCS MAC Layer
            ("dvbTdm", 240), #  DVB Satellite TDM
            ("dvbRcsTdma", 241), #  DVB-RCS TDMA
            ("x86Laps", 242), #  LAPS based on ITU-T X.86/Y.1323
            ("wwanPP", 243), #  3GPP WWAN
            ("wwanPP2", 244), #  3GPP2 WWAN
        ):
        session.add(models.create(models.InterfaceType, name=name, enumeration=enumeration))
    session.commit()

def do_default_environment(session):
    session.add(models.create(models.Environment, name="default"))
    session.commit()

def do_default_group(session):
    session.add(models.create(models.Group, name="testers"))
    session.commit()

def do_capability_groups(session):
    for name in (
        "CPU",
        "system",
        ):
        session.add(models.create(models.CapabilityGroup, name=name))
    session.commit()

def do_capability_types(session):
    for name, desc, group_id, type in (
        ("vmtechnology", "Virtualization support in hardware.", 1, 5),
        ("sleep", "Can be put in low power state (sleep).", 2, 5),
        ):
        session.add(models.create(models.CapabilityType, name=name,
            description=desc, group_id=group_id, value_type=type))
    session.commit()


# addresses can be filled in later by user.
def do_corporations(session):
    for name, desc, in (
        ("AMD", ""),
        ("Dell", "Dell computers."),
        ("Hewlett Packard", "The HP PC company."),
        ("Agilent", "Maker of test and measurement equipment (was HP)."),
        ("Intel", ""),
        ("IBM", ""),
        ("Sun", ""),
        ("Oracle", ""),
        ("Cisco", ""),
        ("Foundry", ""),
        ("Nvidia", ""),
        ("Sonicwall", ""),
        ("Comcast", ""),
        ("Aberdeen", ""),
        ("AT&T", ""),
        ("T-mobile", ""),
        ("American Power Conversion", "APC"),
        ("Belkin", "Maker of console switchers"),
        ("Supermicro", ""),
        ("Apple", ""),
        ("Google", ""),
        ("Microsoft", ""),
        ("Netgear", ""),
        ("Asus", "Maker of PC motherboards."),
        ("Biostar", "Maker of PC motherboards."),
        ("Antec", "Maker of PC cases."),
        ("Tyan", ""),
        ("Newegg", ""),
        ("Amazon", ""),
        ("Central Computer", "PC component reseller."),
        ("Vmware", "Purveyor of virtualization software."),
        ("Mozilla", "The Mozilla foundation."),
        ("Community","a pseudo-corporation that represents the open-source community."),
        ("Custom", "A psuedo-corporation that represents a custom built thing."),
        ):
        session.add(models.create(models.Corporation, name=name, notes=desc))
    session.commit()

def do_riskcategory(session):
    for name, desc, in (
        ("Capability", " Can it perform the required functions?"),
        ("Reliability", " Will it work well and resist failure in all required situations?"),
        ("Usability", " How easy is it for a real user to use the product?"),
        ("Performance", " How speedy and responsive is it?"),
        ("Installability", " How easily can it be installed onto its target platform?"),
        ("Compatibility", " How well does it work with external components & configurations?"),
        ("Supportability", " How economical will it be to provide support to users of the product?"),
        ("Testability", " How effectively can the product be tested?"),
        ("Maintainability", " How economical will it be to build, fix or enhance the product?"),
        ("Portability", " How economical will it be to port or reuse the technology elsewhere?"),
        ("Localizability", " How economical will it be to publish the product in another language?"),
        ):
        session.add(models.create(models.RiskCategory, name=name, description=desc))
    session.commit()


#def do_XXX(session):
#    for name, desc, in (
#        ("XXX", "XXX"),
#        ):
#        session.add(models.create(models.XXX, name=name, description=desc))
#    session.commit()


def create_db(url):
    url = urlparse.UniversalResourceLocator(url, True)
    scheme = url.scheme
    if scheme == "postgresql":
        cmd = 'sudo su postgres -c "createuser --host %s --createdb --no-superuser --no-createrole %s"' % (url.host, url.user)
        os.system(cmd)
        cmd = 'sudo su postgres -c "createdb --host %s --owner %s --encoding utf-8 %s"' % (url.host, url.user, url.path[1:])
        os.system(cmd)
    else:
        raise NotImplementedError("unhandled scheme: {}".format(scheme))


def do_config(session):
    rn = models.create(models.Config, name="root", user=None, parent=None,
            value=aid.NULL)
    session.add(rn)
    flags = models.create(models.Config, name="flags", user=None, container=rn,
            value=aid.NULL)
    session.add(flags)
    session.commit()
    root = config.Container(session, rn)
    flags = config.Container(session, flags)
    flags.VERBOSE = 0 # levels of verbosity
    flags.DEBUG = 0 # levels of debugging
    flags.INTERACTIVE = False # Don't run interactive tests also, by default
    root["logbasename"] = "testrun.log"
    root["logfiledir"] = "/var/tmp"
    root["reportbasename"] = "-"
    root["resultsdirbase"] = '/var/www/localhost/htdocs/testresults'
    root["documentroot"] = "/var/www/localhost"
    # this one, at least, will have to be changed by installer.
    root["baseurl"] = "http://localhost"

    ui = root.add_container("userinterfaces")
    ui.default = ("UI.UserInterface", "IO.ConsoleIO", "UI.DefaultTheme")
    ui.console = ("UI.UserInterface", "IO.ConsoleIO", "UI.DefaultTheme")

    reports = root.add_container("reports")
    reports.default = ("StandardReport", "-", "text/ansi")
    reports.ansi = ("StandardReport", "-", "text/ansi; charset=utf8")
    reports.database = ("pycopia.reports.database.DatabaseReport",)
    reports.email = ("pycopia.reports.Email.EmailReport", "text/html", None)
    reports.html = ("StandardReport", "$username-$runnertimestamp", "text/html")
    reports.full = [
            ("StandardReport", "-", "text/ansi; charset=utf8"),
            ("StandardReport", "$username-$runnertimestamp", "text/html")
            ]
    reports.production = [
            ("StandardReport", "-", "text/ansi; charset=utf8"),
            ("StandardReport", "$username-$runnertimestamp", "text/html"),
            ("pycopia.reports.database.DatabaseReport",),
            ]
    controllers = root.add_container("controllers")
    selenium = root.add_container("selenium")
    selenium.host = "localhost"
    selenium.port = 4444
    selenium.browser = "firefox"
    session.commit()


def init_database(argv):
    try:
        url = argv[1]
    except IndexError:
        from pycopia import basicconfig
        cf = basicconfig.get_config("database.conf")
        url = cf["DATABASE_URL"]
    create_db(url)

    db = create_engine(unicode(url))
    tables.metadata.bind = db
    tables.metadata.create_all()
    db.close()

    SM = models.create_sessionmaker(url)
    dbsession = SM()
    try:
        do_schedules(dbsession)
        do_functional_areas(dbsession)
        do_attribute_types(dbsession)
        do_env_attribute_types(dbsession)
        do_language(dbsession)
        do_country(dbsession)
        do_equipment_category(dbsession)
        do_interface_types(dbsession)
        do_default_environment(dbsession)
        do_default_group(dbsession)
        do_software_category(dbsession)
        do_capability_groups(dbsession)
        do_capability_types(dbsession)
        do_corporations(dbsession)
        do_riskcategory(dbsession)
        do_config(dbsession)
    finally:
        dbsession.close()



if __name__ == "__main__":
    init_database(sys.argv)

