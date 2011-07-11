//    Copyright (C) 2010 Keith Dart <keith@dartworks.biz>
//
//    This library is free software; you can redistribute it and/or
//    modify it under the terms of the GNU Lesser General Public
//    License as published by the Free Software Foundation; either
//    version 2.1 of the License, or (at your option) any later version.
//
//    This library is distributed in the hope that it will be useful,
//    but WITHOUT ANY WARRANTY; without even the implied warranty of
//    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
//    Lesser General Public License for more details.

/**
 * @fileoverview Editor for TestSuite objects.
 * Depends on db.js and ui.js.
 *
 * @author keith@dartworks.biz (Keith Dart)
 */


/**
 * loadTestSuiteApp loads into the content area the base markup for the
 * TestSuite editor. The the TestSuiteApp the currentapp object.
 */
function loadTestSuiteApp() {
  loadApp(TestSuiteApp, "content");
  forEach(document.images, icons.setIconMouseover);
};


/**
 * TestSuiteApp the primary TestSuite editor object.
 */
function TestSuiteApp() {
  this.model = getDBModel("TestSuite");
  this.currentsuite = null;
  this._draggables = [];
  this._csdraggables = [];
  this._droppables = [];
  this.root = DIV({id: "testsuiteapp", "class": "applet"});
  var buttonbar = DIV({id: "buttonbar", class: "buttonbar"});
  // add/create icon and trash icon
  var addicon = icons.getIcon("add");
  connect(addicon, "onclick", bind(this.createTestSuite, this));
  buttonbar.appendChild(addicon);
  var trash = icons.getIcon("trash");
  var drp = new Droppable(trash, {
      accept: ["testsuite_item"],
      ondrop: bind(this._dropOnDelete, this),
      activeclass: "dragtarget",
      });
  this._droppables.push(drp);
  buttonbar.appendChild(trash);
  // major sections.
  this.testsuites = DIV({id: "testsuites"});
  this.cscontent = DIV({id: "dbmodelinstance"});
  this.testcase_list = DIV({id: "choicelist"});
  this.root.appendChild(buttonbar);
  this.root.appendChild(this.testsuites);
  this.root.appendChild(this.cscontent);
  this.root.appendChild(this.testcase_list);
  this.updateTestSuiteList();
  this._drstarth = connect(Draggables, "start", bind(this._dragstart, this));
  this._drendh = connect(Draggables, "end", bind(this._dragend, this));
};

/**
 * Reload, or reset, the app to it's initial condition.
 */
TestSuiteApp.prototype.reload = function() {
  this._disconnect();
  placeContent("testsuites", null);
  placeContent("dbmodelinstance", null);
  placeContent("choicelist", null);
  this.updateTestSuiteList();
};



/** 
 * Undo anything TestSuiteSetApp set in the page.
 */
TestSuiteApp.prototype.destroy = function() {
  disconnect(this._drstarth);
  disconnect(this._drendh);
  this._drstarth = null;
  this._drendh = null;
  this._disconnect();
  this._destroyDraggables();
  this._destroyDroppables();
  this._destroyTSDraggables();
  forEach($("buttonbar").childNodes, function(el) {disconnectAll(el);});
  placeContent("testsuites", null);
  placeContent("dbmodelinstance", null);
  placeContent("choicelist", null);
  placeContent("buttonbar", null);
};

TestSuiteApp.prototype._disconnect = function() {
  var csl = $("testsuites_list");
  if (csl) {
    forEach(csl.childNodes, function(el) {disconnectAll(el.childNode);});
  };
};

/**
 * Force a load of the list of TestSuite entries into the editor list.
 */
TestSuiteApp.prototype.updateTestSuiteList = function() {
  if (!this.model.initialized) { // model has not initialized yet...
    var waiter = wait(0.5); // need some time for model metadata to load.
    waiter.addCallback(bind(this.updateTestSuiteList, this));
  } else {
    var d = this.model.all();
    d.addCallbacks(bind(this._fillTestSuiteList, this), bind(this._errorTestSuiteList, this));
  };
};

TestSuiteApp.prototype._errorTestSuiteList = function(err) {
    console.error(err);
};

TestSuiteApp.prototype._fillTestSuiteList = function(thelist) {
  this._destroyDraggables();
  this._destroyTSDraggables();
  this._disconnect();
  var ul_cs = UL({"id": "testsuites_list", "class": "selectlist"});
  for (var i = 0; i < thelist.length; i++) {
    var obj = thelist[i];
    var clkable = SPAN({"class": "clickable"}, obj.toString());
    var li = LI({"class": "testsuite_item"}, clkable);
    li.setAttribute("id", obj.get_id());
    connect(clkable, "onclick", bind(this._loadTestSuiteHandler, this));
    // Make the item draggable to the trash.
    var dbl = new Draggable(li, {
      starteffect: noop,
      endeffect: noop,
      revert: bind(this._dragrevert, this),
      scroll: window,
      });
    ul_cs.appendChild(li);
    this._csdraggables.push(dbl);
  };
  placeContent("testsuites", ul_cs);
};


/**
 * Destroy previously set draggable.
 *
 * Since the MochiKit Draggables and Droppables controllers keeps a
 * reference to all controlled objects they must be destroyed before adding
 * new ones.  Otherwise, they accumulate (leak).
 */

TestSuiteApp.prototype._destroyDraggables = function() {
  var draggables = this._draggables;
  this._draggables = [];
  while (draggables.length > 0) {
    var dbl = draggables.pop();
    dbl.destroy();
  };
};

TestSuiteApp.prototype._destroyTSDraggables = function() {
  var draggables = this._csdraggables;
  this._csdraggables = [];
  while (draggables.length > 0) {
    var dbl = draggables.pop();
    dbl.destroy();
  };
};

TestSuiteApp.prototype._destroyDroppables = function() {
  var droppables = this._droppables;
  this._droppables = [];
  while (droppables.length > 0) {
    var dp = droppables.pop();
    dp.destroy();
  };
};

/**
 * Make an element draggable according to this editor's style.
 */
TestSuiteApp.prototype._getDraggable = function(el) {
 var draggable = new Draggable(el, {snap: 14,
    starteffect: noop,
    endeffect: noop,
    revert: bind(this._dragrevert, this),
    scroll: window,
    });
 this._draggables.push(draggable);
 return draggable;
};

TestSuiteApp.prototype._loadTestSuiteHandler = function(ev) {
  ev.stop();
  var csid = ev.src().parentNode.id.split("_")[1];
  this.loadTestSuite(csid);
};

/**
 * Load a TestSuite row view into view area and makes it the current
 * test suite.
 *
 * @param {Number} csid The TestSuite database ID.
 */
TestSuiteApp.prototype.loadTestSuite = function(csid) {
  this._destroyDraggables();
  var d = this.model.get(csid);
  d.addCallback(bind(this._fillTestSuite, this));
};

TestSuiteApp.prototype._fillTestSuite = function(cs) {
  this.currentsuite = cs;
  // fill a map for faster filtering later.
  this.hastestcases = {};
  var testcases = cs.data.testcases;
  for (var i = 0; i < testcases.length; i++) {
    this.hastestcases[testcases[i].data.id] = true;
  };
  replaceChildNodes(this.cscontent, cs);
  try {
    var namerow = getFirstElementByTagAndClassName("tr", "VARCHAR", this.cscontent);
    var namedata = namerow.getElementsByTagName("td")[1];
    setEditable(namedata, bind(this._changeName, this));
  }
  catch (e) { 
    console.error(e.name, e.message);
    return;
  };
  var ul = this.cscontent.getElementsByTagName("ul")[0];
  setElementClass(ul, "draglist");
  ul.setAttribute("id", "ts_testcases");
  var drp = new Droppable(ul, {
      accept: ["testcases"],
      ondrop: bind(this._dropOnSet, this),
      activeclass: "dragtarget",
      });
  this._droppables.push(drp);
  forEach(ul.childNodes, bind(function(li) {
                             setElementClass(li, "settestcase"); 
                             var draggable = this._getDraggable(li);
                             draggable.targetid = "cslist_list";
                         }, this)
         );
  var cd = this.model.get_choices("testcases");
  cd.addCallback(bind(this._fillChoices, this));
};

TestSuiteApp.prototype._changeName = function(editable, text) {
  var d = window.db.updaterow(this.model.name, this.currentsuite.data.id, {name: text});
  d.addCallback(bind(this._nameUpdated, this, editable, text));
};

TestSuiteApp.prototype._nameUpdated = function(editable, newtext, rv) {
  if (rv) {
    editable.finish(newtext);
    // also update the TestSuite list with the new name (in the clickable span).
    var csid = this.currentsuite.get_id();
    replaceChildNodes($(csid).firstChild, newtext);
  } else {
    editable.revert();
  };
};

TestSuiteApp.prototype._fillChoices = function(choices) {
  // var choices = this.model.get_choices("testcases");
  var choicesnode = UL({"class": "draglist", id: "cslist_list"});
  var drp = new Droppable(choicesnode, {
      accept: ["settestcase"],
      ondrop: bind(this._dropOnChoices, this),
      activeclass: "dragtarget",
      });
  this._droppables.push(drp);
  for (var i = 0; i < choices.length; i++) {
    if (!this.hastestcases[choices[i][0]]) {
      var li = this._draggableLI(choices[i][0], choices[i][1]);
      choicesnode.appendChild(li);
    };
  };
  placeContent("choicelist", choicesnode);
};

TestSuiteApp.prototype._dropOnSet = function(dragelement, dropelement, ev) {
  this._dorevert = false;
  var cid = parseInt(dragelement.id.split("_")[1]);
  var d = window.db.related_add(this.model.name, this.currentsuite.data.id, 
                              "testcases", "TestCase", cid);
  d.addCallback(bind(this._updateItemNode, this, dragelement, dropelement));
};

TestSuiteApp.prototype._dropOnChoices = function(dragelement, dropelement, ev) {
  this._dorevert = false;
  var cid = parseInt(dragelement.id.split("_")[1]);
  var d = window.db.related_remove(this.model.name, this.currentsuite.data.id, 
                                            "testcases", "TestCase", cid);
  d.addCallback(bind(this._updateItemNode, this, dragelement, dropelement));
};

TestSuiteApp.prototype._updateItemNode = function(dragelement, dropelement, result) {
  if (result) { // positive response: ok to update item lists and elements.
    // remove visual element from source. This code re-uses the Element
    // node and draggable control, updated as appropriate.
    var par = dragelement.parentNode;
    par.removeChild(dragelement);
    if (hasElementClass(dragelement, "settestcase")) {
      setElementClass(dragelement, "testcases");
    } else {
      setElementClass(dragelement, "settestcase");
    };
    setNodeAttribute(dragelement, "style", 'position: relative;');
    dropelement.appendChild(dragelement);
    // update target ID
    var dragged = this.dragged;
    if (dragged.targetid == "cslist_list") {
      dragged.targetid = "ts_testcases";
    } else {
      dragged.targetid = "cslist_list";
    };
  } else {
    window.alert("Unable to update TestSuite, please try again.");
  };
  delete this.dragged;
};

TestSuiteApp.prototype._dragstart = function(draggable, ev) {
  this.dragged = draggable;
  this._dorevert = true;
};

TestSuiteApp.prototype._dragend = function(draggable) {
  setStyle(draggable.element, {"left": 0, "top": 0});
};

TestSuiteApp.prototype._dragrevert = function(dragelement, ev) {
  return this._dorevert;
};

TestSuiteApp.prototype._draggableLI = function(id, text) {
  var li = LI({"id": "cid_" + id, "class": "testcases"}, 
                       text);
  var draggable = this._getDraggable(li);
  draggable.targetid = "ts_testcases";
  return li;
};

/**
 * Create a new TestSuite, user is prompted to name it.
 * The use can then edit it as normal.
 */
TestSuiteApp.prototype.createTestSuite = function() {
  var newname = window.prompt("Name for new test suite?", "new_testsuite");
  var d = window.db.create(this.model.name, {name: newname});
  d.addCallback(bind(this._createHandler, this, newname));
};

TestSuiteApp.prototype._createHandler = function(newname, csid) {
  // Update set selection list.
  var clkable = SPAN({class: "clickable"}, newname);
  var li = LI({"class": "testsuite_item"}, clkable);
  li.setAttribute("id", this.model.name + "_" + csid[0]);
  connect(clkable, "onclick", bind(this._loadTestSuiteHandler, this));
  var dbl = new Draggable(li, {
    starteffect: noop,
    endeffect: noop,
    revert: bind(this._dragrevert, this),
    scroll: window,
    });
  $("testsuites_list").appendChild(li);
  this._csdraggables.push(dbl);
  this.loadTestSuite(csid[0]); // now, user can edit it.
};

TestSuiteApp.prototype._dropOnDelete = function(draggable, droppable, ev) {
  // don't do anything if the clickable was dragged.
  if (ev.target().tagName != "span") {
    if (window.confirm("Are you sure you want to delete " + 
          scrapeText(draggable) + "?")) {
      this._dorevert = false;
      this.dragged.destroy();
      delete this.dragged;
      var csid = parseInt(draggable.id.split("_")[1]);
      var d = window.db.deleterow(this.model.name, csid);
      d.addCallback(bind(this._delete_cb, this, csid));
    };
  };
};

TestSuiteApp.prototype._delete_cb = function(csid, disp) {
  if (disp) {
    // If deleted CS is currently displayed, reset the whole list.
    if (this.currentsuite && this.currentsuite.data.id == csid) {
      this.updateTestSuiteList();
      placeContent("dbmodelinstance", null);
      placeContent("choicelist", null);
    } else { // else, just remove the entry from the testsuites_list.
      var li = $(this.model.name + "_" + csid);
      disconnectAll(li.childNode);
      disconnectAll(li);
      swapDOM(li, null);
    };
  } else {
    window.alert("Could not delete test suite: " + csid);
  };
};


function testSuiteInit() {
  if (!window.db.initialized) { 
    var waiter = wait(0.5); 
    waiter.addCallback(testSuiteInit);
  } else {
    loadTestSuiteApp();
  };
};


connect(window, "onload", testSuiteInit);

// vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
