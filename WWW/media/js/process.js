



function showProcStat(procstat) {
  if (procstat == null) {
    return;
  }
  var tbl = TABLE(null, 
    THEAD(null, rowDisplay(["Stat", "Value"])),
    TBODY(null, map(rowDisplay, items(procstat))));
  showContent(tbl);
}

function PythonError(reqerror) {
  var exclist = evalJSONRequest(reqerror.req);
  var exc = exclist[0];
  var val = exclist[1];
  // list of (filename, line_number, function_name, text) 
  var tracebacklist = exclist[2];

  var tb = TABLE(null, 
    THEAD(null, rowDisplay(["file", "line", "function", "text"])),
    TBODY(null, map(rowDisplay, tracebacklist)));
  var p = P(null, reqerror.req.response, BR(), 
      exc, BR(), val, BR(), tb);
  showContent(p);
}


function getProcStat(pid) {
  var d = loadJSONDoc("/process/cb/procstat", {"pid": pid})
  d.addCallbacks(showProcStat, PythonError);
}

function procRowDisplay(row) {
  return TR(null, 
           TD(null, 
             A({"href":"javascript:getProcStat("+row[1]+")"}, row[1])), 
           TD(null, row[0]));
}

function showProcList(proclist) {
  if (proclist == null) {
    return;
  }
  var sidebar = document.getElementById("sidebar");
  var tbl = TABLE(null, 
    THEAD(null, rowDisplay(["PID", "Command"])),
    TBODY(null, map(procRowDisplay, sorted(proclist))));
  if (sidebar.hasChildNodes()) {
    sidebar.replaceChild(tbl, sidebar.lastChild);
  } else {
    sidebar.appendChild(tbl);
  }
}

function getProcList() {
  var d = loadJSONDoc("/process/cb/proclist");
  d.addCallbacks(showProcList, PythonError);
  return false;
}


function refreshTaskList() {
  getProcList();
  callLater(120, refreshTaskList); // auto-refresh...
}

function showMessageAndListenAgain(msg) {
  showMessage(msg);
  messageListener();
}

function messageListener() {
  var d = loadJSONDoc("/process/cb/message");
  d.addCallbacks(showMessageAndListenAgain, PythonError);
}

function showCommandOutput(rr) {
  var ok = rr[0];
  if (ok) {
    var output = rr[1];
    showContent(P(null, PRE(null, output.output)));
  }
}

function getCommandOutput(pid) {
  var d = loadJSONDoc("/process/cb/getoutput", {"pid": pid})
  d.addCallbacks(showCommandOutput, PythonError);
}

function doCommandForm() {
  var inp = document.getElementById("id_cmd");
  var d = loadJSONDoc("/process/cb/spawn", {"cmd": inp.value})
  d.addCallbacks(getCommandOutput, PythonError);
  return false;
}



