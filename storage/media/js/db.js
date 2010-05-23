// vim:ts=2:sw=2:softtabstop=2:smarttab:expandtab

/**
 * Client side code for general pycopia model access. 
 * MochiKit is used here  <http://www.mochikit.com/> (loaded seperately).
 *
 * Depends on:
 *   MochiKit.js
 *   proxy.js
 */



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


/////////////// DB objects. ////////////////////

/**
 * DBModel holds table metadata as defined in a pycopia.db.models.py file.
 */
function DBModel(modelname) {
  this.initialized = false;
  this.name = modelname;
  this._meta = {};
  this._meta.fields = [];
  this._meta.fieldmap = {}; // For faster access to fields by name.
  this.objects = new DBManager(this);
  var d = db.get_table(modelname);
  d.addCallback(bind(this._fillModelMetadata, this));
};

DBModel.prototype._fillModelMetadata = function(info) {
  for (var i = 1; i < info.length; i++) { 
    // skip first header line (i = 1) since it contains only column names.
    var fieldinfo = info[i];
    // ["name", "coltype", "Default"]
    var internaltype = fieldinfo[1];
    var field = new window[internaltype](fieldinfo[0], fieldinfo[2]);
    this._meta.fields.push(field);
    this._meta.fieldmap[field.attname] = field;
  };
  this.initialized = true;
};

DBModel.prototype.getField = function(fieldname) {
  return this._meta.fieldmap[fieldname];
};

DBModel.prototype.get_choices = function(fieldname) {
  var field = this._meta.fieldmap[fieldname];
  return field.get_choices(this.name);
};

/**
 * Getter for DBModel object. This object is cached, for
 * performance.
 */
function getDBModel(modelname) {
  var model = window.modelcache[modelname];
  if (typeof(model) == "undefined") {
    model = new DBModel(modelname);
    window.modelcache[modelname] = model;
  };
  return model;
};

/**
 * DBModelInstance represents an instance of a DBModel, which is a
 * table row.
 */
function DBModelInstance(model, str, row) {
  this.data = row;
  this._model = model
  this._str_ = str;
  this.isdeleted = false;
};

DBModelInstance.prototype.toString = function() {
  return this._str_;
};

DBModelInstance.prototype.__dom__ = function(node) {
  // TODO object view registry. This is the default, generic generator.
  var tbl = TABLE(null, createDOM("caption", null, this._model.name),
              THEAD(null,
                TR(null,
                  TH(null, "Field"), TH(null, "Value"))));
  var body = TBODY(null);
  tbl.appendChild(body);
  var fields = this._model._meta.fields;
  for (var i = 0; i < fields.length; i++) {
    var field = fields[i];
    var tr = TR(null,
                  TD(null, field.attname),
                  TD(null, this.data[field.attname].toString()));
    body.appendChild(tr);
  };
  return tbl;
};


DBModelInstance.prototype.get_id = function() {
    return this._model.name + "_" + this.data.id
};

/**
 * Delete the instance in the database.
 */
DBModelInstance.prototype.deleterow = function() {
  if (!this.isdeleted) {
    var d = db.deleterow(this.model.name, this.data.id);
    d.addCallback(bind(this._delete_db, this));
  };
};

DBModelInstance.prototype._delete_cb = function(deleted) {
  this.isdeleted = deleted;
};

/**
 * Save any changed data.
 */
DBModelInstance.prototype.save = function() {
  if (!this.isdeleted) {
    // TODO filter out m2m data.
    var d = db.update(this.model.name, this.data.id, this.data);
    d.addCallback(bind(this._save_cb, this));
  };
};

DBModelInstance.prototype._save_cb = function(disp) {
  this._savedok = disp;
};


/**
 * DBManager object proxies a DB Manager.
 *
 */

function DBManager(dbmodel) {
  this._modelname = dbmodel.name;
  this._meta = dbmodel._meta;
};

/**
 * Instantiate row data. Bind model metadata.
 */

DBManager.prototype.all = function() {
  return db.get_all(this._modelname);
};

DBManager.prototype.filter = function(kwargs) {
  return db.get_filter(this._modelname, kwargs);
};

DBManager.prototype.get = function(kwargs) {
   var d =  db.table_get(this._modelname, kwargs);
   return d;
};

DBManager.prototype.exclude = function(kwargs) {
  // TODO implement
};

DBManager.prototype.order_by = function(fields) {
  // TODO implement
};

DBManager.prototype.distinct = function(fields) {
  // TODO implement
};

DBManager.prototype.sql = function(query) {
  // TODO implement
};

// query-set-methods-that-do-not-return-queries
DBManager.prototype.create = function(kwargs) {
  // TODO implement
};

DBManager.prototype.get_or_create = function(kwargs) {
  // TODO implement
};

DBManager.prototype.count = function() {
  // TODO implement
};

DBManager.prototype.in_bulk = function(id_list) {
  // TODO implement
};


//////////////////////////////////////////////////////////////////////////////
// These objects below map to db field classes.


function BaseField() {
  this.choices = null;
};
BaseField.prototype.get_choices = function(modelname) {
  if (!this.choices) {
    var d = db.get_choices(modelname, this.attname);
    d.addCallback(partial(_recieveChoices, this));
  };
  return this.choices; // may be null
};

_FieldPrototype = new BaseField();

function AutoField(name, def, help) {
  this.attname = name;
  this.default_value = def;
  this.help_text = help;
};
AutoField.prototype = _FieldPrototype;

function BooleanField(name, def, help) {
  this.attname = name;
  this.default_value = def;
  this.help_text = help;
};
BooleanField.prototype = _FieldPrototype;

function CharField(name, def, help) {
  this.attname = name;
  this.default_value = def;
  this.help_text = help;
};
CharField.prototype = _FieldPrototype;

function IntegerField(name, def, help) {
  this.attname = name;
  this.default_value = def;
  this.help_text = help;
};
IntegerField.prototype = _FieldPrototype;

function NullBooleanField(name, def, help) {
  this.attname = name;
  this.default_value = def;
  this.help_text = help;
};
NullBooleanField.prototype = _FieldPrototype;

function TextField(name, def, help) {
  this.attname = name;
  this.default_value = def;
  this.help_text = help;
};
TextField.prototype = _FieldPrototype;

function ForeignKey(name, def, help) {
  this.attname = name;
  this.default_value = def;
  this.help_text = help;
};
ForeignKey.prototype = _FieldPrototype;


function RelationProperty(name, help) {
  this.attname = name;
  this.help_text = help;
  this.choices = null;
};

RelationProperty.prototype.get_choices = function(modelname) {
  if (!this.choices) {
    var d = db.get_choices(modelname, this.attname);
    d.addCallback(partial(_recieveChoices, this));
  };
  return this.choices; // may be null
};

_recieveChoices = function(obj, cl) {
  obj.choices = cl;
};


//////////////////////////////////////////////////////////////////////////////
///////// Model object view builders.

//////////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////////
///// Deserialization handlers

function jsonConvertRow(obj) {
  var modelname =  obj._class_
  var model = getDBModel(modelname);
  var inst =  new DBModelInstance(model, obj._str_, obj.value);
  var m2mfs = model._meta.many_to_many;
  for (var i = 0; i < m2mfs.length; i++) {
    var field = m2mfs[i];
    obj.value[field.attname] = map(jsonConvertRow, obj.value[field.attname]);
  };
  return inst;
};

function jsonDBCheck(obj) {
  return obj._class_.indexOf("DM_") == 0; // XXX
};

//////////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////////
///////// Model metadata inspector applet.

/**
 * Update list of table names in nav bar (column, actually).
 */
function loadModelMetaApp() {
  loadApp(ModelMetaApp);
};

/**
 * This application object simples fills the extra navigation area with a
 * list of all db model names. Click on one to view its metadata in a
 * table. 
 */
function ModelMetaApp() {
  this.reload();
};

ModelMetaApp.prototype.reload = function() {
  var d = db.get_tables();
  d.addCallback(bind(this.dbFillExtra, this));
};

ModelMetaApp.prototype.destroy = function() {
  placeContent("extra", null);
};

/**
 * Fill extra navigation with table names.
 *
 * @param {Array} modelnames List of table names to insert in nav bar.
 *
 */
ModelMetaApp.prototype.dbFillExtra = function(modelnames) {
  var tbl = TABLE(null, 
    createDOM("caption", null, "Table Names"),
    THEAD(null, TR(null, TH(null, "Name"))),
    TBODY(null, map(_dbTableNameDisplay, modelnames))
    );
  placeContent("extra", tbl);
};

/**
 * Mapping function to return a table name row with link to call
 * dbTableInfo.
 * @param {String} modelname Name of table.
 *
 */
function _dbTableNameDisplay(modelname) {
  return TR(null,
            TD(null,
              A({"href":"javascript:dbTableInfo('"+modelname+"')"}, 
                 modelname)
             )
           );
};

/**
 * Get table metadata from server.
 * @param {String} modelname Name of table.
 *
 */
function dbTableInfo(modelname) {
  var d = db.get_table(modelname);
  d.addCallback(partial(showTableInfo, modelname));
};

/**
 * Callback for dbTableInfo. Puts table of db metadata into content
 * area.
 * @param {Array} info List of table info, plus a heading line.
 *
 */
function showTableInfo(modelname, info) {
  var tbl = TABLE(null,
    createDOM("caption", null, modelname),
    THEAD(null, headDisplay(info[0])),
    TBODY(null, map(rowDisplay, info.slice(1))));
  placeContent("content", tbl);
};


// Places object into content area (content div).
function showContent(obj) {
  var content = document.getElementById("content");
  if (content.hasChildNodes()) {
    content.replaceChild(obj, content.lastChild);
  } else {
    content.appendChild(obj);
  }
}


function showMessage(obj) {
  if (obj) {
    log(obj);
    var text = document.createTextNode(obj.toString());
    var msgarea = document.getElementById("messages");
    if (msgarea.hasChildNodes()) {
      msgarea.replaceChild(text, msgarea.lastChild);
    } else {
      msgarea.appendChild(text);
    }
  }
}


function notifyResult(rowid, result) {
  if (result[0]) {
    removeElement($("rowid_" + rowid));
    showMessage("Item '" + result[1] + "' deleted.");
  } else {
    window.alert("There was a problem deleting this item. " + result[1]);
  };
};

function doDeleteRow(tablename, rowid) {
  if (window.confirm("Delete instance of " + tablename +"?")) {
    var d = window.db.deleterow(tablename, rowid);
    d.addCallback(partial(notifyResult, rowid));
  }
}

/**
 * Initializer adds the "db" object that has methods that map the the
 * exported methods on the server side.
 */

function dbInit() {
  window.db = new PythonProxy("/storage/api/");
  window.modelcache = {};
  jsonEvalRegistry.register("dbmodel", jsonDBCheck, jsonConvertRow);
};

function dbCleanup() {
  delete window.db;
  delete window.modelcache;
  jsonEvalRegistry.unregister("dbmodel");
};

// Initialize our stuff after page load.
connect(window, "onload", dbInit);
connect(window, "onunload", dbCleanup);

