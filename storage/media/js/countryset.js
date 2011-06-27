
function loadCountrySetApp() {
  loadApp(CountrySetApp, "content");
  forEach(document.images, setIconMouseover);
};

/**
 * CountrySetApp object. Encapsulates the mini-application that allows one
 * to manage the CountrySet table in the database. This is a relatively simple
 * example of the Pycopia web APIs.
 *
 * The editor uses a drag-and-drop interface to add countries to the set
 * (or remove them). All operations are committed in the database
 * immediately, there are no "OK", or "submit" buttons. 
 *
 * The name is an editable field. Just click on it to change the name.
 * The change updates the database also.
 *
 * The user can create a new CountrySet by clicking the add icon/button.
 * The user is prompted for a name to name the new set, and it is
 * immediatly created. The user can then edit it as normal.
 *
 * Mousing over the list of CountrySet entries displays a red X icon that
 * a user can drag to the trash to delete it.
 */

function CountrySetApp() {
  this.model = getDBModel("CountrySet");
  this.currentset = null;
  this._draggables = [];
  this._csdraggables = [];
  this._droppables = [];
  this.root = DIV({id: "countrysetapp", "class": "applet"});
  var buttonbar = DIV({id: "buttonbar", class: "buttonbar"});
  // add/create icon and trash icon
  var addicon = getIcon("add");
  connect(addicon, "onclick", bind(this.createCountrySet, this));
  buttonbar.appendChild(addicon);
  var trash = getIcon("trash");
  var drp = new Droppable(trash, {
      accept: ["countryset_item"],
      ondrop: bind(this._dropOnDelete, this),
      activeclass: "dragtarget",
      });
  this._droppables.push(drp);
  buttonbar.appendChild(trash);
  // major sections.
  this.countrysets = DIV({id: "countrysets"});
  this.cscontent = DIV({id: "dbmodelinstance"});
  this.country_list = DIV({id: "choicelist"});
  this.root.appendChild(buttonbar);
  this.root.appendChild(this.countrysets);
  this.root.appendChild(this.cscontent);
  this.root.appendChild(this.country_list);
  this.updateCountrySetList();
  this._drstarth = connect(Draggables, "start", bind(this._dragstart, this));
  this._drendh = connect(Draggables, "end", bind(this._dragend, this));
};

/**
 * Reload, or reset, the app to it's initial condition.
 */
CountrySetApp.prototype.reload = function() {
  this._disconnect();
  placeContent("countrysets", null);
  placeContent("dbmodelinstance", null);
  placeContent("choicelist", null);
  this.updateCountrySetList();
};

/** 
 * Undo anything CountrySetApp set in the page.
 */
CountrySetApp.prototype.destroy = function() {
  disconnect(this._drstarth);
  disconnect(this._drendh);
  this._drstarth = null;
  this._drendh = null;
  this._disconnect();
  this._destroyDraggables();
  this._destroyDroppables();
  this._destroyCSDraggables();
  forEach($("buttonbar").childNodes, function(el) {disconnectAll(el);});
  placeContent("countrysets", null);
  placeContent("dbmodelinstance", null);
  placeContent("choicelist", null);
  placeContent("buttonbar", null);
};

CountrySetApp.prototype._disconnect = function() {
  var csl = $("countrysets_list");
  if (csl) {
    forEach(csl.childNodes, function(el) {disconnectAll(el.childNode);});
  };
};

/**
 * Force a load of the list of CountrySet entries into the editor list.
 */
CountrySetApp.prototype.updateCountrySetList = function() {
  if (!this.model.initialized) { // model has not initialized yet...
    var waiter = wait(0.5); // need some time for model metadata to load.
    waiter.addCallback(bind(this.updateCountrySetList, this));
  } else {
    var d = this.model.all();
    d.addCallback(bind(this._fillCountrySetList, this));
  };
};

CountrySetApp.prototype._fillCountrySetList = function(thelist) {
  this._destroyDraggables();
  this._destroyCSDraggables();
  this._disconnect();
  var ul_cs = UL({"id": "countrysets_list", "class": "selectlist"});
  for (var i = 0; i < thelist.length; i++) {
    var obj = thelist[i];
    var clkable = SPAN({"class": "clickable"}, obj.toString());
    var li = LI({"class": "countryset_item"}, clkable);
    li.setAttribute("id", obj.get_id());
    connect(clkable, "onclick", bind(this._loadCountrySetHandler, this));
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
  placeContent("countrysets", ul_cs);
};


/**
 * Destroy previously set draggable.
 *
 * Since the MochiKit Draggables and Droppables controllers keeps a
 * reference to all controlled objects they must be destroyed before adding
 * new ones.  Otherwise, they accumulate (leak).
 */

CountrySetApp.prototype._destroyDraggables = function() {
  var draggables = this._draggables;
  this._draggables = [];
  while (draggables.length > 0) {
    var dbl = draggables.pop();
    dbl.destroy();
  };
};

CountrySetApp.prototype._destroyCSDraggables = function() {
  var draggables = this._csdraggables;
  this._csdraggables = [];
  while (draggables.length > 0) {
    var dbl = draggables.pop();
    dbl.destroy();
  };
};

CountrySetApp.prototype._destroyDroppables = function() {
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
CountrySetApp.prototype._getDraggable = function(el) {
 var draggable = new Draggable(el, {snap: 14,
    starteffect: noop,
    endeffect: noop,
    revert: bind(this._dragrevert, this),
    scroll: window,
    });
 this._draggables.push(draggable);
 return draggable;
};

CountrySetApp.prototype._loadCountrySetHandler = function(ev) {
  ev.stop();
  var csid = ev.src().parentNode.id.split("_")[1];
  this.loadCountrySet(csid);
};

/**
 * Load a CountrySet row view into view area and makes it the current
 * country set.
 *
 * @param {Number} csid The CountrySet database ID.
 */
CountrySetApp.prototype.loadCountrySet = function(csid) {
  this._destroyDraggables();
  var d = this.model.get(csid);
  d.addCallback(bind(this._fillCountrySet, this));
};

CountrySetApp.prototype._fillCountrySet = function(cs) {
  this.currentset = cs;
  // fill a map (hascountries) for faster filtering later.
  this.hascountries = {};
  var countries = cs.data.countries;
  for (var i = 0; i < countries.length; i++) {
    this.hascountries[countries[i].data.id] = true;
  };
  replaceChildNodes(this.cscontent, cs);
  try {
    var namerow = getFirstElementByTagAndClassName("tr", "VARCHAR", this.cscontent);
    var namedata = namerow.getElementsByTagName("td")[1];
    setEditable(namedata, bind(this._changeName, this));
  }
  catch (e) { 
    logError(e);
  };
  var ul = this.cscontent.getElementsByTagName("ul")[0];
  setElementClass(ul, "draglist");
  ul.setAttribute("id", "cs_countries");
  var drp = new Droppable(ul, {
      accept: ["countries"],
      ondrop: bind(this._dropOnSet, this),
      activeclass: "dragtarget",
      });
  this._droppables.push(drp);
  forEach(ul.childNodes, bind(function(li) {
                             setElementClass(li, "setcountry"); 
                             var draggable = this._getDraggable(li);
                             draggable.targetid = "cslist_list";
                         }, this)
         );
  var cd = this.model.get_choices("countries");
  cd.addCallback(bind(this._fillChoices, this));
};

CountrySetApp.prototype._changeName = function(editable, text) {
  var d = window.db.updaterow(this.model.name, this.currentset.data.id, {name: text});
  d.addCallback(bind(this._nameUpdated, this, editable, text));
};

CountrySetApp.prototype._nameUpdated = function(editable, newtext, rv) {
  if (rv) {
    editable.finish(newtext);
    // also update the countryset list with the new name (in the clickable
    // span).
    var csid = this.currentset.get_id();
    replaceChildNodes($(csid).firstChild, newtext);
  } else {
    editable.revert();
  };
};

CountrySetApp.prototype._fillChoices = function(choices) {
  // var choices = this.model.get_choices("countries");
  var choicesnode = UL({"class": "draglist", id: "cslist_list"});
  var drp = new Droppable(choicesnode, {
      accept: ["setcountry"],
      ondrop: bind(this._dropOnChoices, this),
      activeclass: "dragtarget",
      });
  this._droppables.push(drp);
  for (var i = 0; i < choices.length; i++) {
    if (!this.hascountries[choices[i][0]]) {
      var li = this._draggableLI(choices[i][0], choices[i][1]);
      choicesnode.appendChild(li);
    };
  };
  placeContent("choicelist", choicesnode);
};

CountrySetApp.prototype._dropOnSet = function(dragelement, dropelement, ev) {
  this._dorevert = false;
  var cid = parseInt(dragelement.id.split("_")[1]);
  var d = window.db.related_add(this.model.name, this.currentset.data.id, 
                              "countries", "Country", cid);
  d.addCallback(bind(this._updateItemNode, this, dragelement, dropelement));
};

CountrySetApp.prototype._dropOnChoices = function(dragelement, dropelement, ev) {
  this._dorevert = false;
  var cid = parseInt(dragelement.id.split("_")[1]);
  var d = window.db.related_remove(this.model.name, this.currentset.data.id, 
                                            "countries", "Country", cid);
  d.addCallback(bind(this._updateItemNode, this, dragelement, dropelement));
};

CountrySetApp.prototype._updateItemNode = function(dragelement, dropelement, result) {
  if (result) { // positive response: ok to update item lists and elements.
    // remove visual element from source. This code re-uses the Element
    // node and draggable control, updated as appropriate.
    var par = dragelement.parentNode;
    par.removeChild(dragelement);
    if (hasElementClass(dragelement, "setcountry")) {
      setElementClass(dragelement, "countries");
    } else {
      setElementClass(dragelement, "setcountry");
    };
    setNodeAttribute(dragelement, "style", 'position: relative;');
    dropelement.appendChild(dragelement);
    // update target ID
    var dragged = this.dragged;
    if (dragged.targetid == "cslist_list") {
      dragged.targetid = "cs_countries";
    } else {
      dragged.targetid = "cslist_list";
    };
  } else {
    window.alert("Unable to update CountrySet, please try again.");
  };
  delete this.dragged;
};

CountrySetApp.prototype._dragstart = function(draggable, ev) {
  this.dragged = draggable;
  this._dorevert = true;
};

CountrySetApp.prototype._dragend = function(draggable) {
  setStyle(draggable.element, {"left": 0, "top": 0});
};

CountrySetApp.prototype._dragrevert = function(dragelement, ev) {
  return this._dorevert;
};

CountrySetApp.prototype._draggableLI = function(id, text) {
  var li = LI({"id": "cid_" + id, "class": "countries"}, 
                       text);
  var draggable = this._getDraggable(li);
  draggable.targetid = "cs_countries";
  return li;
};

/**
 * Create a new CountrySet, user is prompted to name it.
 * The use can then edit it as normal.
 */
CountrySetApp.prototype.createCountrySet = function() {
  var newname = window.prompt("Name for new CountrySet?", "new_countryset");
  var d = window.db.create(this.model.name, {name: newname});
  d.addCallback(bind(this._createHandler, this, newname));
};

CountrySetApp.prototype._createHandler = function(newname, csid) {
  // Update set selection list.
  var clkable = SPAN({class: "clickable"}, newname);
  var li = LI({"class": "countryset_item"}, clkable);
  li.setAttribute("id", this.model.name + "_" + csid[0]);
  connect(clkable, "onclick", bind(this._loadCountrySetHandler, this));
  var dbl = new Draggable(li, {
    starteffect: noop,
    endeffect: noop,
    revert: bind(this._dragrevert, this),
    scroll: window,
    });
  $("countrysets_list").appendChild(li);
  this._csdraggables.push(dbl);
  this.loadCountrySet(csid[0]); // now, user can edit it.
};

CountrySetApp.prototype._dropOnDelete = function(draggable, droppable, ev) {
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

CountrySetApp.prototype._delete_cb = function(csid, disp) {
  if (disp) {
    // If deleted CS is currently displayed, reset the whole list.
    if (this.currentset && this.currentset.data.id == csid) {
      this.updateCountrySetList();
      placeContent("dbmodelinstance", null);
      placeContent("choicelist", null);
    } else { // else, just remove the entry from the countrysets_list.
      var li = $(this.model.name + "_" + csid);
      disconnectAll(li.childNode);
      disconnectAll(li);
      swapDOM(li, null);
    };
  } else {
    window.alert("Could not delete CountrySet " + csid);
  };
};


connectOnce(window, "onload", function(ev) {
    connectOnce(window, "dbready", function () {
        loadCountrySetApp();
      }
    );
});

