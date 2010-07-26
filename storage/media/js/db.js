// vim:ts=2:sw=2:softtabstop=2:smarttab:expandtab

/**
 * Client side code for general pycopia model access. 
 * MochiKit is used here  <http://www.mochikit.com/> (loaded seperately).
 *
 * Depends on:
 *   MochiKit.js
 *   proxy.js
 *   ui.js
 */

/////////////// DB objects. ////////////////////

/**
 * DBModel holds table metadata as defined in a .../pycopia/db/models.py file.
 * dbmodel.name is modelname
 * dbmodel._Meta is a list of metadata tuples:
        coltype, colname, default, m2m, nullable, uselist
 */
function DBModel(modelname) {
  this.initialized = false;
  this.name = modelname;
  this._meta = {};
  var d = window.db.get_table_metadata_map(modelname);
  d.addCallback(bind(this._fillModelMetadata, this));
};

DBModel.prototype._fillModelMetadata = function(metamap) {
  this._meta = metamap;
  this.initialized = true;
};

DBModel.prototype.get_column = function(fieldname) {
  return this._meta[fieldname];
};

DBModel.prototype.get_choices = function(fieldname) {
  return window.db.get_choices(this.name, fieldname)
};

DBModel.prototype.all = function() {
  return window.db.query(this.name, {})
};

DBModel.prototype.get = function(entry_id) {
  return window.db.get_row(this.name, entry_id);
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
  var metadata = this._model._meta;
  for (var colname in metadata) {
    var coldata = metadata[colname];
    if (coldata[0] == "RelationProperty") {
      var tr = TR(null,
                    TD(null, colname),
                    TD(null, 
                      UL(null, map(function (obj) {
                                return LI({id: obj.get_id()}, obj.toString());
                              },
                            this.data[colname])
                      )
                    )
               );
    } else {
      var tr = TR({"class": coldata[0]},
                    TD(null, colname),
                    TD(null, this.data[colname].toString()));
    }
    body.appendChild(tr);
  };
  return tbl;
};

/**
 * Return a useful Node id. 
 */
DBModelInstance.prototype.get_id = function() {
    return this._model.name + "_" + this.data.id
};

/**
 * Delete the instance in the database.
 */
DBModelInstance.prototype.deleterow = function() {
  if (!this.isdeleted) {
    var d = window.db.deleterow(this.model.name, this.data.id);
    d.addCallback(bind(this._delete_db, this));
  };
};

DBModelInstance.prototype._delete_cb = function(deleted) {
  this.isdeleted = deleted;
};

DBModelInstance.prototype.set = function(colname, value) {
  this.data[colname] = value;
};

/**
 * Save any changed data.
 */
DBModelInstance.prototype.save = function() {
  if (!this.isdeleted) {
    var d = window.db.updaterow(this.model.name, this.data.id, this.data);
    d.addCallback(bind(this._save_cb, this));
  };
};

DBModelInstance.prototype._save_cb = function(disp) {
  this._savedok = disp;
};



//////////////////////////////////////////////////////////////////////////////
///////// Model object view builders.

//////////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////////
///// Deserialization handlers

function jsonConvertRow(obj) {
  if (obj == null) {
    return obj;
  }
  var modelname =  obj._class_;
  var model = getDBModel(modelname);
  if (model.initialized) {
    for (var colname in model._meta) {
      // coltype, colname, default, m2m, nullable, uselist
      var value = obj.value[colname];
      if (typeof(value) != "undefined") {
        if (model._meta[colname][0] == "RelationProperty") {
          if (model._meta[colname][5] == true) { // uselist
            obj.value[colname] = map(jsonConvertRow, value);
          } else {
            obj.value[colname] = jsonConvertRow(value);
          };
        };
      };
    }
  };
  var inst =  new DBModelInstance(model, obj._str_, obj.value);
  return inst;
};

function jsonDBCheck(obj) {
  return obj._dbmodel_ == true;
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
  this.root = DIV({id: "modelmetaapp", "class": "applet"});
};

ModelMetaApp.prototype.reload = function() {
  var d = window.db.get_tables();
  d.addCallback(bind(this.dbFillExtra, this));
};

ModelMetaApp.prototype.destroy = function() {
  placeContent("messages", null);
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
    TBODY(null, map(_dbTableNameDisplay, keys(modelnames)))
    );
  placeContent("messages", tbl);
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
  var d = window.db.get_table_metadata(modelname);
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
    THEAD(null, headDisplay(
        ["Type", "Name", "Default", "Many2Many", "Nullable", "Uselist"])),
    TBODY(null, map(rowDisplay, info)));
  placeContent("content", tbl);
};



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

function getUIData() {
  var d = window.db.get_uidata();
  d.addCallback(function (uidata) {window.uiData = uidata;});
};

/**
 * Initializer adds the "db" object that has methods that map the the
 * exported methods on the server side.
 */

function dbInit() {
  window.db = new PythonProxy("/storage/api/", getUIData);
  window.modelcache = {};
  jsonEvalRegistry.register("dbmodel", jsonDBCheck, jsonConvertRow);
};

function dbCleanup() {
  delete window.uiData;
  delete window.db;
  delete window.modelcache;
  jsonEvalRegistry.unregister("dbmodel");
};

// Initialize our stuff after page load.
connect(window, "onload", dbInit);
connect(window, "onunload", dbCleanup);

