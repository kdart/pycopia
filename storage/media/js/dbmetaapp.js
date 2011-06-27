//////////////////////////////////////////////////////////////////////////////
///////// Model metadata inspector applet.


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
    CAPTION(null, "Table Names"),
    THEAD(null, TR(null, TH(null, "Name"))),
    TBODY(null, map(function (modelname) {
            return TR(null,
                      TD(null,
                        A({"href":"javascript:dbTableInfo('"+modelname+"')"}, 
                           modelname))
            );
          }, keys(modelnames)))
    );
  placeContent("extra", tbl);
};

/**
 * Get table metadata from server.
 * @param {String} modelname Name of table.
 *
 */
function dbTableInfo(modelname) {
  var d = window.db.get_table_metadata(modelname);
  var heading = ["Type", "Colname", "Default", "Many2Many", "nullable", "Uselist", "Collection"]; 
  d.addCallback( function (info) {
      var tbl = TABLE(null,
          CAPTION(null, modelname),
          THEAD(null, headDisplay(heading)),
          TBODY(null, map(rowDisplay, info)),
          TFOOT(null, headDisplay(heading))
        );
      placeContent("modelmetaapp", tbl);
    }
  );
};

connectOnce(window, "onload", function(ev) {
    connectOnce(window, "dbready", function () {
        loadApp(ModelMetaApp, "content");
      }
    );
});

