#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
#
#    Copyright (C) 1999-2006  Keith Dart <keith@kdart.com>
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.

"""
A collection of Web browser user agent strings.
Culled from actual apache log file.

"""

# The key value is a simplified name you use in scripts. The value is the
# actual user agent string.

USER_AGENTS = {
  'cern': 'CERN-LineMode/2.15 libwww/2.17b3',
  'dfind': 'DFind',
  'atw_crawl': 'FAST-WebCrawler/3.6 (atw-crawler at fast dot no; http://fast.no/support/crawler.asp)',
  'gigabot': 'Gigabot/2.0; http://www.gigablast.com/spider.html',
  'links': 'Links (2.0; Linux 2.4.18-6mdkenterprise i686; 80x36)',
  'lynx': 'Lynx/2.8.5dev.3 libwww-FM/2.14 SSL-MM/1.4.1 OpenSSL/0.9.6c',
  'motorola': 'MOT-V600/0B.09.3AR MIB/2.2 Profile/MIDP-2.0 Configuration/CLDC-1.0',
  'mscontrol': 'Microsoft URL Control - 6.00.8862',
  'jeeves': 'Mozilla/2.0 (compatible; Ask Jeeves/Teoma; +http://sp.ask.com/docs/about/tech_crawling.html)',
  'slurp': 'Mozilla/3.0 (Slurp/si; slurp@inktomi.com; http://www.inktomi.com/slurp.html)',
  'msie4_w95': 'Mozilla/4.0 (compatible; MSIE 4.01; Windows 95)',
  'msie5_w2k': 'Mozilla/5.0 (compatible; MSIE 5.01; Win2000)',
  'msie501_w98': 'Mozilla/4.0 (compatible; MSIE 5.01; Windows 98)',
  'msie501_nt': 'Mozilla/4.0 (compatible; MSIE 5.01; Windows NT 5.0)',
  'msie50_w98': 'Mozilla/4.0 (compatible; MSIE 5.0; Windows 98; DigExt)',
  'msie50_nt': 'Mozilla/4.0 (compatible; MSIE 5.0; Windows NT 5.0)',
  'msie51_mac': 'Mozilla/4.0 (compatible; MSIE 5.14; Mac_PowerPC)',
  'msie55_nt': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT 5.0; T312461)',
  'msie6_98': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows 98)',
  'msie6_w98_crazy': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows 98; Crazy Browser 1.0.5)',
  'msie6_w98': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows 98; Win 9x 4.90)',
  'msie6_nt': 'Mozilla/4.0 (compatible; MSIE 6.01; Windows NT 5.0)',
  'msie6_net': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
  'msie6_net_mp': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0; MathPlayer 2.0; .NET CLR 1.0.3705; .NET CLR 1.1.4322)',
  'msie6_net_infopath': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0; T312461; .NET CLR 1.1.4322; InfoPath.1)',
  'msie6': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)',
  'msie6_2': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; Q312469)',
  'msie6_sp1': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)',
  'msie6_net_sp1': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322)',
  'msie6_net2_sp1': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 2.0.50727)',
  'msie6_net_sp1_2': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50215)',
  'msie6_net_sp1_maxthon': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; Maxthon; .NET CLR 1.1.4322)',
  'msie6_net_sp1_naver': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; Naver Desktop Search)',
  'msie6_net_ypc': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; YPC 3.2.0; FunWebProducts; .NET CLR 1.0.3705)',
  'msie6_net_ypc2': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; YPC 3.2.0; FunWebProducts; .NET CLR 1.0.3705; yplus 5.1.02b)',
  'zyborg': 'Mozilla/4.0 compatible ZyBorg/1.0 Dead Link Checker (wn.dlc@looksmart.net; http://www.WISEnutbot.com)',
  'mozilla_mac': 'Mozilla/4.72 (Macintosh; I; PPC)',
  'netscape4_en': 'Mozilla/4.76 [en] (X11; U; Linux 2.4.17 i686)',
  'mozilla5': 'Mozilla/5.0',
  'safari_intel': 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X; en) AppleWebKit/418 (KHTML, like Gecko) Safari/417.9.3',
  'safari_ppc': 'Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/418 (KHTML, like Gecko) Safari/417.9.2',
  'mozilla_w_de': 'Mozilla/5.0 (Windows; U; Win 9x 4.90; de-AT; rv:1.7.8) Gecko/20050511',
  'netscape6_w': 'Mozilla/5.0 (Windows; U; Win 9x 4.90; en-US; VaioUSSum01) Gecko/20010131 Netscape6/6.01',
  'firefox10_w_de': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; de-DE; rv:1.7.10) Gecko/20050717 Firefox/1.0.6',
  'firefox15_w_gb': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.0.3) Gecko/20060426 Firefox/1.5.0.3',
  'firefox10_w': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.12) Gecko/20050915 Firefox/1.0.7',
  'netscape8_w': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.5) Gecko/20060127 Netscape/8.1',
  'firefox15_w': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.0.3) Gecko/20060426 Firefox/1.5.0.3',
  'firefox15_w_goog': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.0.3; Google-TR-3) Gecko/20060426 Firefox/1.5.0.3',
  'firefox15_w_fr': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; fr; rv:1.8.0.3) Gecko/20060426 Firefox/1.5.0.3',
  'firefox15_w_it': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.0.3) Gecko/20060426 Firefox/1.5.0.3',
  'firefox15_w_ru': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; ru; rv:1.8.0.3) Gecko/20060426 Firefox/1.5.0.3',
  'mozilla10': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.0) Gecko/00200203',
  'firefox10_lmand': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.7.10) Gecko/20050921 Firefox/1.0.7 Mandriva/1.0.6-15mdk (2006.0)',
  'firefox10_ldeb': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.7.10) Gecko/20060424 Firefox/1.0.4 (Debian package 1.0.4-2sarge6)',
  'firefox10_fed': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.7.12) Gecko/20060202 Fedora/1.0.7-1.2.fc4 Firefox/1.0.7',
  'epiphany16': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.7.13) Gecko/20060418 Epiphany/1.6.1 (Ubuntu) (Ubuntu package 1.0.8)',
  'firefox15_l': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.2) Gecko/20060308 Firefox/1.5.0.2',
  'firefox15_lpango': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.2) Gecko/20060419 Fedora/1.5.0.2-1.2.fc5 Firefox/1.5.0.2 pango-text',
  'firefox15_ldeb': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.3) Gecko/20060326 Firefox/1.5.0.3 (Debian-1.5.dfsg+1.5.0.3-2)',
  'becomebot': 'Mozilla/5.0 (compatible; BecomeBot/3.0; MSIE 6.0 compatible; +http://www.become.com/site_owners.html)',
  'googlebot': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
  'konqueror': 'Mozilla/5.0 (compatible; Konqueror/3.0.0-10; Linux)',
  'konqueror1': 'Mozilla/5.0 (compatible; Konqueror/3.0; i686 Linux; 20020919)',
  'konqueror2': 'Mozilla/5.0 (compatible; Konqueror/3.1-rc4; i686 Linux; 20020504)',
  'konqueror3': 'Mozilla/5.0 (compatible; Konqueror/3.5; Linux; i686; en_US) KHTML/3.5.2 (like Gecko) (Debian)',
  'yahoo': 'Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)',
  'galeon1': 'Mozilla/5.0 Galeon/1.2.1 (X11; Linux i686; U;) Gecko/0',
  'mz5mac_ja': 'Mozilla/5.001 (Macintosh; N; PPC; ja) Gecko/25250101 MegaCorpBrowser/1.0 (MegaCorp, Inc.)',
  'mozilla5_w': 'Mozilla/5.001 (windows; U; NT4.0; en-us) Gecko/25250101',
  'mozilla5_irix': 'Mozilla/5.25 Netscape/5.0 (X11; U; IRIX 6.3 IP32)',
  'mozilla9': 'Mozilla/9.876 (X11; U; Linux 2.2.12-20 i686, en) Gecko/25250101 Netscape/5.432b1 (C-MindSpring)',
  'nextgen1': 'NextGenSearchBot 1 (for information visit http://www.zoominfo.com/NextGenSearchBot)',
  'opera6_l': 'Opera/6.0 (Linux 2.4.18-6mdk i686; U)  [en]',
  'opera6_w': 'Opera/6.04 (Windows XP; U)  [en]',
  'opera7_w': 'Opera/7.0 (Windows NT 5.1; U)  [en]',
  'python': 'Python/2.4 (X11; U; Linux i686; en-US)',
  'slysearch': 'SlySearch/1.3 (http://www.slysearch.com)',
  'surveybot': 'SurveyBot/2.3 (Whois Source)',
  'syntryx': 'Syntryx ANT Scout Chassis Pheromone; Mozilla/4.0 compatible crawler',
  'gecko': 'TinyBrowser/2.0 (TinyBrowser Comment) Gecko/20201231',
  'wget': 'Wget/1.10.2',
  'wget_rh': 'Wget/1.10.2 (Red Hat modified)',
  'lwp': 'lwp-trivial/1.41',
  'msnbot': 'msnbot/1.0 (+http://search.msn.com/msnbot.htm)',
}

