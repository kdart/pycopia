/**
 * General purpose user interface library for Pycopia web interfaces.
 */

/**
 * icons namespace, manages icons, supports three sizes: small, medium, and large. Small are 10x10,
 * medium are 16x16, and large are 24x24 pixels. It maps a simple name to a file name using the
 * ICONMAP key in the uiData object. This is fetched from server side at load time by an app.
 * Large icons support two images for mouseover effects.
 */

icons = {
    getIconPath: function(basename) {
      return "/media/images/"+basename;
    },
    /**
     * Set mouseover callbacks for icon images.
     * @param {Element} img The image object to set.
     */
    setIconMouseover: function(img) {
      if (img.src.indexOf("icon_") >= 0) { // src initially set by server.
        var namepair = uiData["ICONMAP"]["large"][img.alt];
        // If _isactive_ part defined, add mouseover.
        if (namepair && namepair[0]) {
          connect(img, "onmouseover", 
                  partial(icons.iconChange, icons.getIconPath(namepair[0])));
          connect(img, "onmouseout", 
                  partial(icons.iconChange, icons.getIconPath(namepair[1])));
        };
      };
    },
    /**
     * Provide alternate graphic for mouseover effect. This is a Mochikit
     * event handler.
     * @param {String} src The base file name of a icon.
     * @param {CustomEvent} ev The Mochikit event.
     */
    iconChange: function(src, ev) {
      ev.target().src = src;
    },
    /**
     * Construct in icon image element.
     * @param {String} simplename The name of the icon (index into ICONMAP table).
     * @param {String} size The size name, "large", "medium", or "small".
     * @return {Element} img The image element.
     */
    getIcon: function(simplename, size) {
        var size = size || "large";
        return {large: icons.getLargeIcon,
                medium: icons.getMediumIcon,
                small: icons.getSmallIcon}[size](simplename);
    },
    getLargeIcon: function(simplename) {

        var activeInactive = uiData["ICONMAP"]["large"][simplename];
        if (!activeInactive) {
            activeInactive = uiData["ICONMAP"]["large"]["default"];
        }
        var img = IMG({
                    src: icons.getIconPath(activeInactive[1]), 
                    alt: simplename, 
                    width: "24", 
                    height: "24"
                  });
        if (activeInactive[0]) {
          connect(img, "onmouseover", 
                  partial(icons.iconChange, icons.getIconPath(activeInactive[0])));
          connect(img, "onmouseout", 
                  partial(icons.iconChange, icons.getIconPath(activeInactive[1])));
        };
        return img;
    },
    /**
     * Construct a medium size icon image element.
     * @param {String} simplename The name of the icon (index into ICONMAPtable).
     * @return {Element} img The image element.
     */
    getMediumIcon: function(simplename) {
      var iconname = uiData["ICONMAP"]["medium"][simplename];
      if (!iconname) {
        iconname = uiData["ICONMAP"]["medium"]["default"];
      }
      var img = IMG({
                  src: icons.getIconPath(iconname), 
                  alt: simplename, 
                  width: "16", 
                  height: "16"
                });
      return img;
    },
    /**
     * Construct a small icon image element.
     * @param {String} simplename The name of the icon (index into ICONMAP_SMALL 
     * table).
     * @return {Element} img The image element.
     */
    getSmallIcon: function(simplename) {
      var iconname = uiData["ICONMAP"]["small"][simplename];
      if (!iconname) {
        iconname = uiData["ICONMAP"]["small"]["default"];
      }
      var img = IMG({
                  src: icons.getIconPath(iconname), 
                  alt: simplename, 
                  width: "10", 
                  height: "10"
                });
      return img;
    }
};


/**
 * Places object as sole object in some content div.
 *
 * @param {String} id ID of element to place object into.
 * @param {Node} obj The DOM node to be placed. If you pass a null value
 * it is the same as removing content from the content object.
 */
function placeContent(id, obj) {
  var content = document.getElementById(id);
  if (content.hasChildNodes()) {
    if (obj) {
      content.replaceChild(obj, content.lastChild);
    } else {
      content.removeChild(content.lastChild);
    };
  } else {
    if (obj) {
      content.appendChild(obj);
    };
  };
};

/**
 * Append an Node object to the element, given the ID.
 * @param {String} id The ID of the node to append to.
 * @param {Element} obj The Element to append.
 */
function appendContent(id, obj) {
  var content = document.getElementById(id);
  content.appendChild(obj);
};

function insertContent(id, obj, /* optional */ pos) {
  pos = pos || 0;
  var content = document.getElementById(id);
  var refnode = content.childNodes[pos];
  content.insertBefore(obj, refnode);
};

/**
 * General purpose table row constructor.
 * @param {Array} row List of objects to place into row cells.
 * @return {Element} tr a TR node filled with TD.
 */
function rowDisplay(row) {
  return TR(null, map(partial(TD, null), row));
};

function headDisplay(row) {
  return TR(null, map(partial(TH, null), row));
};

/**
 * Load an application into the content space. The application should have
 * a root attribute that has the root element (usually a DIV) containing
 * the application.
 *
 * @param {Object} The application object to load. 
 *
 * Sets the global "currentapp" name to the application.
 */
function loadApp(appobject, area) {
  if (window.currentapp === appobject) {
    window.currentapp.reload();
  } else {
    unloadApp(area);
    var app = new appobject();
    placeContent(area, app.root); // All Apps should have a root element.
    window.currentapp = app;
  };
};

/** 
 * Remove any loaded applet.
 */
function unloadApp(area) {
  if (typeof(window.currentapp) != "undefined") {
    var app = window.currentapp;
    delete window.currentapp;
    app.destroy();
  };
  placeContent(area, null);
};


/**
 * Button handler to confirm selection and call url. Display good or bad result.
 * This is a generalized confirmation dialog with outcome reported. It
 * corresponds to the AddAskConfirmationAndGet method on the client side.
 * @param {String} question The question to present to user in confirm dialog.
 * @param {String} url The URL to fetch (JSON) if answer is yes.
 * @param {String} goodmsg Message to present to user if operation successful.
 * @param {String} badmsg Message to present to user if operation NOT successful.
 * @param {Object} mevent MochiKit event object from button callback.
 */
function askConfirmationAndGet(question, url, goodmsg, badmsg, mevent) {
  if (window.confirm(question)) {
    var d = loadJSONDoc(url);
    d.addCallback(partial(notifyResult, goodmsg, badmsg));
  };
};

/**
 * Works with askConfirmationAndGet to provide the go/nogo feedback to user.
 */
function notifyResult(goodmsg, badmsg, result) {
  if (result) {
    window.alert(goodmsg);
    window.opener.location.href = window.opener.location.href; /* force reload */
  } else {
    window.alert(badmsg);
  };
};


/**
 * Editable makes any text node editable.
 * Instantiate with original text, and a callback function that's called
 * when the text is edited.
 *
 * The callback is called with this editable and the new text as
 * parameters. It is the callback's responsibility to decide to call the
 * editable "finish" method, or the "revert" method (allows it to validate the
 * entry). It may also alter the text, and supplies it to the finish
 * method.
 *
 * @param {String} text The text to be displayed, and default value when editing.
 * @param {Function} callback A callback that will be called when user
 * edits the text.
 */

function Editable(text, callback) {
  this._callback = callback;
  this.element = SPAN({class: "editable"}, text);
  connect(this.element, "onclick", bind(this._editableHandler, this));
};

Editable.prototype.__dom__ = function(node) {
  return this.element;
};

/**
 * Transform the text area into an editable form.
 * Use this if your script wants to explicitly set it to editable.
 * Normally, this happens when the user clicks on the editable text area.
 */
Editable.prototype.makeEditable = function () {
  var text = scrapeText(this.element);
  var inp = INPUT({name: "currentedit", 
                   maxlength: "255", 
                   value: text});
  var frm = FORM({method: "post", action: "."},  // values not used, but required.
                inp);
  swapDOM(this.element, frm);
  connect(frm, "onsubmit", bind(this._editableSubmitHandler, this));
  inp.focus();
  disconnectAll(this.element);
  this.element = frm;
  this._oldvalue = text;
  return frm;
};

/**
 * Callback should call this with the new value of the text. This finishes
 * the edit and reverts back to non-edit mode.
 *
 * @param {String} newvalue, the new value for the text area.
 */
Editable.prototype.finish = function(newvalue) {
  var sp = SPAN({class: "editable"}, newvalue);
  connect(sp, "onclick", bind(this._editableHandler, this));
  disconnectAll(this.element);
  swapDOM(this.element, sp);
  this.element = sp;
  delete this._oldvalue;
};

/**
 * Callback should call this if new text is unacceptable, or some
 * operation with it could not performed. Reverts text to original value.
 */
Editable.prototype.revert = function() {
  this.finish(this._oldvalue);
};

Editable.prototype._editableSubmitHandler = function(ev) {
  ev.stop();
  var contents = formContents(this.element);
  var newvalue = contents[1][0]; // first value, the INPUT field.
  if (newvalue != this._oldvalue) {
    this._callback(this, newvalue);
  } else {
    this.revert();
  };
  return false;
};

Editable.prototype._editableHandler = function(ev) {
  this.makeEditable();
};


/**
 * Allow text inside an Element node to be editable. Sets the text node
 * inside the given node to be controlled by an Editable instance.
 *
 * @param {Element} node, The node that should contain one Text node as its
 * immediate child.
 * @param {Function} callback, The callback that will be called when text
 * is edited.
 */
function setEditable(node, callback) {
  var text = scrapeText(node);
  var editable = new Editable(text, callback);
  replaceChildNodes(node, editable);
  return editable;
};

// Places object into content area (content div).
function showContent(obj, areaname) {
    var areaname = areaname || "content";
    var content = document.getElementById(areaname);
    if (content.hasChildNodes()) {
      content.replaceChild(obj, content.lastChild);
    } else {
      content.appendChild(obj);
    }
}


function showMessage(obj, areaname) {
    var areaname = areaname || "messages";
    if (obj) {
      var text = document.createTextNode(obj.toString());
      var msgarea = document.getElementById(areaname);
      if (msgarea.hasChildNodes()) {
        msgarea.replaceChild(text, msgarea.lastChild);
      } else {
        msgarea.appendChild(text);
      }
    }
}

