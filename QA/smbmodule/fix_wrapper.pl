#!/usr/bin/env perl -i.bak
while(<>) {
   if(/"OO:(\w+?)_(\w+?)_(set|get)"/o) {
      print;
      $_ = <>;
      print;
      $conv=<>;
      $_=<>;
      if(/^\s*\{\s*$/o) {
         print "/* $conv*/\n";
      } else {
         print $conv;
      }
   }
   print;
}


