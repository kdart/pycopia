//////////////////////////////////////////////////////////////////////////////
///////// Model metadata inspector applet.


/**
 * This application object simples fills the sidebar navigation area with a
 * list of all db model names. Click on one to view its metadata in a
 * table. 
 */
function ModelMetaApp() {
  this.reload();
  this.root = DIV({id: "modelmetaapp", "class": "applet"});
};

ModelMetaApp.prototype.reload = function() {
  var d = window.db.get_tables();
  d.addCallback(bind(this.dbFillSidebar, this));
};

ModelMetaApp.prototype.destroy = function() {
  placeContent("messages", null);
};

/**
 * Fill Sidebar navigation with table names.
 *
 * @param {Array} modelnames List of table names to insert in nav bar.
 *
 */
ModelMetaApp.prototype.dbFillSidebar = function(modelnames) {
  var tbl = TABLE(null, 
    CAPTION(null, "Table Names"),
    THEAD(null, TR(null, TH(null, "Name"))),
    TBODY(null, map(function (modelname) {
            return TR(null,
                      TD(null,
                        A({"href":"javascript:dbTableInfo('"+modelname+"')"}, 
                           modelname))
            );
          }, sorted(keys(modelnames))))
    );
  placeContent("sidebar", tbl);
};

/**
 * Get table metadata from server.
 * @param {String} modelname Name of table.
 *
 */
function dbTableInfo(modelname) {
  var heading = ["Type", "Colname", "Default", "Many2Many", "nullable", "Uselist", "Collection"]; 
  var d = window.db.get_table_metadata(modelname);
  d.addCallback( function (info) {
      var tbl = TABLE(null,
          CAPTION(null, modelname),
          THEAD(null, headDisplay(heading)),
          TBODY(null, map(rowDisplay, map(function (o) {return [o.colname, o.coltype, o["default"],
                o.m2m, o.nullable, o.uselist, o.collection]}, info))),
          TFOOT(null, headDisplay(heading))
        );
      placeContent("modelmetaapp", tbl);
    }
  );
  d.addErrback(function(e) {console.error(e);});
};

connectOnce(window, "onload", function(ev) {
    connectOnce(window, "dbready", function () {
        loadApp(ModelMetaApp, "content");
      }
    );
});

