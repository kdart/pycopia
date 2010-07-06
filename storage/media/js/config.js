
/**
 * Initial setup of active icons in the config table.
 * @param {Element} img The image tag to check and set handlers.
 */
function setupConfigIcons(img) {
  setIconMouseover(img);
}

/**
 * Handler for value editor form. This actually POSTs the form, and checks
 * the return value. Return 'false' to prevent browser from submitting the
 * form itself. This prevents the browser from updating its page.
 */
function configFormAction() {
  var d = doXHR("/storage/config/update/", {
                  method: "POST",
                  headers: {
                            "Content-Type": "application/x-www-form-urlencoded"
                           },
                  sendContent: queryString(formContents(this))
                  }
                );
  d.addCallbacks(partial(configUpdateDone, this), configBadUpdate);
  return false; // forces browser not to submit form, since it's done here.
}

/**
 * Error callback for configFormAction. Just log the error.
 */
function configBadUpdate(req) {
  logError(req);
}

/**
 * Callback handles response from server after setting new value.
 * A list of two elements is returned. The first item is a boolean
 * indicating if the value update was successful or not. The second item
 * is the new value, if successful, or an error message if not.
 * If successful, change the table cell content back to the span with the
 * new value.
 * @param {Element} frm The (dynamic) form object.
 * @param {Object} req The MochiKit XMLHttpRequest object.
 */
function configUpdateDone(frm, req) {
  var resp = evalJSONRequest(req);
  if (resp[0]) {
    var newvalue = resp[1];
    var sp = SPAN({id: frm.configid.value, class: "editable"}, newvalue);
    configSetupEditable(sp);
    disconnectAll(frm);
    swapDOM(frm, sp);
  } 
  else {
    alert(resp[1]); // try again...
  }
}

/**
 * Helper for value edit form builder. Creates the radio button element.
 * @param {Number} seq The sequence number to put in the id.
 * @param {String} label The label string for the button.
 */
function configCreateRadioButton(seq, label) {
  var ID = label+seq
  return LABEL({"for": ID}, label, 
  INPUT({id: ID, type: "radio", name: "valtype", value: seq}), "  ");
}


/**
 * Transform a span containing the current value string into a form
 * allowing it to be changed. The form is submitted with the 'onsubmit'
 * handler only.
 * @param {Element} span The span element to replace with form containing
 * an editable text field.
 */
function configMakeEditable(span) {
  var text = scrapeText(span);
  var inp = INPUT({name: "currentedit", 
                   maxlength: "255", 
                   size: "80", 
                   value: text});
  var frm = FORM({method: "post", action: "update/"}, 
                configCreateRadioButton("0", "Expression"),
                configCreateRadioButton("1", "String"),
                configCreateRadioButton("2", "Integer"),
                configCreateRadioButton("3", "Float"),
                configCreateRadioButton("4", "Boolean"),
                INPUT({type: "hidden", name: "configid", value: span.id}),
                BR(), 
                inp
                );
  frm.elements[0].checked = "checked";
  swapDOM(span, frm);
  frm.onsubmit = configFormAction; // using MochiKit connect doesn't work right here.
  inp.focus();
}


/**
 * The event handler that is called when the user clicks on an "editable"
 * span.
 */
function editableHandler(ev) {
  var orig = configMakeEditable(ev.src());
}

/**
 * Set the onclick handler on a span element.
 * @param {Element} span The span element to replace with form containing
 */
function configSetupEditable(span) {
  connect(span, "onclick", editableHandler)
}


/**
 * Callback attached to delete button/icon. Calls config item delete url
 * on server.
 */
function configDelete(cfId, cfName, ev) {
  if (window.confirm("Delete '" + cfName + "'?")) {
    var d = loadJSONDoc(cfId + "/delete/")
    d.addCallback(partial(alertConfigDelete, cfName, ev.src()));
  }
}


/**
 * Callback that notifies user regarding the status of the delete
 * operation. The table row is removed on success.
 * @param {Element} img The image element that acts as a button. It's
 * parent row is the one to delete.
 * @param {String} cfName The name of the config item.
 * @param {Boolean} isSuccessful indicates if delete operation was
 * successful.
 */
function alertConfigDelete(cfName, img, isSuccessful) {
  if (isSuccessful) {
    disconnectAll(img);
    var tr = getFirstParentByTagAndClassName(img, "tr");
    swapDOM(tr, null);
  } 
  else {
    window.alert("Not able to delete '" + cfName + "'.");
  }
}


/**
 * Initialize the client-side data and DOM for the config admin views.
 * @param {Event} ev The Mochikit event triggered by page load.
 */
function userconfigInit(ev) {
  forEach(document.images, setupConfigIcons);
  forEach(getElementsByTagAndClassName("span", "editable"),
          configSetupEditable);
}


