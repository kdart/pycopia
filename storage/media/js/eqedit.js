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
 * @fileoverview File desc.
 *
 * @author keith@dartworks.biz (Keith Dart)
 * @depends db.js
 */


function TableManager(start, end) {
    this.start = start || 0;
    this.end = end || 20;
    this.colnames = ["id", "name", "serno"];
    bindMethods(this);
}

/**
 * Show a section of the the equipment table. Placed into eqlist div.
 * @param {Number} start the starting limit. Defaults to 1.
 * @param {Number} end The ending limit. Defaults to 20.
 * @return {Node} Return_desc.
 */
TableManager.prototype.Init = function() {
    this.update();
};

TableManager.prototype.update = function() {
    datad = window.db.query("Equipment", {"active":true}, this.colnames, null, this.start, this.end);
    datad.addCallback(this.fillEqtableData);
    datad.addErrback(function (err) {
        if (err instanceof CancelledError) {
            return;
        }
        logError(err);
    });
};

TableManager.prototype.fillEqtableData = function(data) {
    var tbl = TABLE({"class":"sortable"}, CAPTION(null, "Equipment"));
    var thead = THEAD({id:"eqthead"}, headDisplay(this.colnames));
    thead.rows[0].cells[0].classList.add("sorttable_nosort");
    var tbody = TBODY(null);
    tbl.appendChild(thead);
    tbl.appendChild(tbody);
    tbl.appendChild(TFOOT(null, headDisplay(this.colnames)));
    var cycler = cycle(["row1", "row2"]);
    for (var di = 0; di < data.length; di++) {
        var drow = data[di];
        var dbid = drow[0];
        var row = TR({"dbid_id": dbid, "class": cycler.next()});
        row.appendChild(TD(null, A({"href": format("javascript:doDeleteEquipmentRow({0});", dbid)}, getSmallIcon("delete")),
                                 A({"href": format("javascript:doEditEquipmentRow({0});", dbid)}, getSmallIcon("edit"))));
        for (var ri = 1; ri < drow.length; ri++) {
            row.appendChild(TD(null, drow[ri]));
        };
        tbody.appendChild(row);
    }
    placeContent("eqlist", tbl);
    sorttable.makeSortable(tbl);
};

function doEditEquipmentRow(dbid) {
    alert("Not implemented.");
};

function doDeleteEquipmentRow(dbid) {
    alert("Not implemented.");
};


mouseOverFunc = function () {
    addElementClass(this, "over");
};

mouseOutFunc = function () {
    removeElementClass(this, "over");
};

ignoreEvent = function (ev) {
    if (ev && ev.preventDefault) {
        ev.preventDefault();
        ev.stopPropagation();
    } else if (typeof(event) != 'undefined') {
        event.cancelBubble = false;
        event.returnValue = false;
    }
};




/**
 * eqeditInit
 * Start the eqEdit application.
 */
function eqeditInit() {
    var manager = new TableManager();
    window.tablemanager = manager;
    window.eqedit = new PythonProxy("/storage/eqapi/");
    connectOnce(window.eqedit, "proxyready", manager.Init);
};

function eqeditCleanup() {
  // delete window.eqedit;
  delete window.tablemanager;
};

connectOnce(window, "onload", function(ev) {
    connectOnce(window, "dbready", function () {
        eqeditInit();
      }
    );
});
connectOnce(window, "onunload", eqeditCleanup);


// vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
