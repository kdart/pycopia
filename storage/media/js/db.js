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
 * dbmodel._meta is a list of metadata tuples:
        coltype, colname, default, m2m, nullable, uselist, collection
 */

function DBModel(modelname) {
  this.init(modelname);
};


DBModel.prototype.init = function(modelname) {
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


_ColCreators = {
  "textinput": function(node, coldata) {
    tid = "id_" + coldata.colname;
    node.appendChild(LABEL({"for":tid}));
    node.appendChild(INPUT({type:"text", "id": tid}));
  },
  "textarea": function(node, coldata) {
    node.appendChild(
    FIELDSET({"name": coldata.colname}, 
        TEXTAREA({})));
  },
  "bool": function(node, coldata) {
  },
  "pickle": function(node, coldata) {
  },
  "valuetype": function(node, coldata) {
  },
  "relation": function(node, coldata) {
  },
  "testcasestatus": function(node, coldata) {
  },
  "testcasetype": function(node, coldata) {
  },
  "priority": function(node, coldata) {
  },
  "array": function(node, coldata) {
  },
  "bytearray": function(node, coldata) {
  },
  "bit": function(node, coldata) {
  },
  "cidr": function(node, coldata) {
  },
  "inet": function(node, coldata) {
  },
  "date": function(node, coldata) {
  },
  "timestamp": function(node, coldata) {
  },
  "floatingpt": function(node, coldata) {
  },
  "integer": function(node, coldata) {
  },
  "macaddr": function(node, coldata) {
  },
  "numeric": function(node, coldata) {
  },
  "time": function(node, coldata) {
  },
  "uuid": function(node, coldata) {
  },
  "enumtype": function(node, coldata) {
  }
};

// Map column types (including custom types defined by SqlAlchemy API) to DOM constructors.
_Creators = {
    "ARRAY": _ColCreators.array,
    "BIGINT": _ColCreators.textinput,
    "BYTEA": _ColCreators.bytearray,
    "BIT": _ColCreators.bit,
    "BOOLEAN": _ColCreators.bool,
    "CHAR": _ColCreators.textinput,
    "Cidr": _ColCreators.cidr,
    "Inet": _ColCreators.inet,
    "DATE": _ColCreators.date,
    "TIMESTAMP": _ColCreators.timestamp,
    "FLOAT": _ColCreators.floatingpt,
    "INTEGER": _ColCreators.integer,
    "INTERVAL": _ColCreators.textinput,
    "MACADDR": _ColCreators.macaddr,
    "NUMERIC": _ColCreators.numeric,
    "SMALLINT": _ColCreators.integer,
    "VARCHAR": _ColCreators.textinput,
    "TEXT": _ColCreators.textarea,
    "TIME": _ColCreators.time,
    "UUID": _ColCreators.uuid,
    "PickleText": _ColCreators.pickle,
    "ValueType": _ColCreators.valuetype,
    "RelationshipProperty": _ColCreators.relation,
    "TestCaseStatus": _ColCreators.enumtype,
    "TestCaseType": _ColCreators.enumtype,
    "PriorityType": _ColCreators.enumtype,
    "SeverityType": _ColCreators.enumtype,
    "LikelihoodType": _ColCreators.enumtype,
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
 * Represents a NULL value.
 */

function NULL() {
};

NULL.prototype.toString = function() {
  return NBSP;
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
  var tbl = TABLE(null, CAPTION(null, this._model.name),
              THEAD(null,
                TR(null,
                  TH(null, "Field"), TH(null, "Value"))));
  var body = TBODY(null);
  tbl.appendChild(body);
  var metadata = this._model._meta;
  for (var colname in metadata) {
    var colmetadata = metadata[colname];
    var coldata = this.data[colname];
    if (coldata === null) {
      coldata = new NULL();
    };
    if (colmetadata[0] == "RelationshipProperty") {
      if (colmetadata[5] == true) { // uselist
        var tr = TR(null,
                      TD(null, colname),
                      TD(null, 
                        UL(null, map(function (obj) {
                                  return LI({id: obj.get_id()}, obj.toString());
                                }, coldata)
                        )
                      )
                 );
      } else {
        var tr = TR(null,
                      TD(null, colname),
                      TD(null, coldata.toString())
                 );

      };
    } else {
      var tr = TR({"class": colmetadata[0]},
                    TD(null, colname),
                    TD(null, coldata.toString()));
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
    d.addCallback(function(deleted) {this.isdeleted = deleted;});
    return d;
  };
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
    return d;
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
      // coltype, colname, default, m2m, nullable, uselist, collection
      var value = obj.value[colname];
      if (typeof(value) != "undefined") {
        if (model._meta[colname][0] == "RelationshipProperty") {
          if (model._meta[colname][5] == true) { // uselist
            obj.value[colname] = map(jsonConvertRow, value);
          } else {
            obj.value[colname] = jsonConvertRow(value);
          };
        } else {
            obj.value[colname] = convertClasses(value);
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


/**
 * Common database CRUD functions.
 * 
 */

function doDeleteRow(tablename, rowid) {
  if (window.confirm("Delete instance of " + tablename +"?")) {
    var d = window.db.deleterow(tablename, rowid);
    d.addBoth( function (result) {
          if (result[0]) {
            removeElement($("rowid_" + rowid));
            showMessage("Item '" + result[1] + "' deleted.");
          } else {
            window.alert("There was a problem deleting this item. " + result[1]);
          };
        }, 
        function () {
            console.log("Error requesting deletion."); 
            window.alert("Could not delete item.");
          }
    );
    return d;
  }
}

/**
 * Initializer adds the "db" object that has methods that map the the
 * exported methods on the server side. Also gets the user interface data (icon maps, etc.) 
 */

function dbInit() {
  window.modelcache = {};
  jsonEvalRegistry.register("dbmodel", jsonDBCheck, jsonConvertRow);
  window.db = new PythonProxy("/storage/api/");
  connectOnce(window.db, "proxyready", function () {
        var d = window.db.get_uidata();
        d.addCallback(function (uidata) {
            window.uiData = uidata;
            signal(window, "dbready");
          });
      }
  );
};

function dbCleanup() {
  delete window.uiData;
  delete window.db;
  delete window.modelcache;
  jsonEvalRegistry.unregister("dbmodel");
};

// Initialize our stuff after page load.
connectOnce(window, "onload", dbInit);
connectOnce(window, "onunload", dbCleanup);

