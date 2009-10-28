

/** Changes the job isscheduled icon state. Sets the appropriate icon
 * for the state of the job, This also sets the mouseover handlers.
 * @param {Element} img The associated img element (set from partial function).
 * @param {Object} jobdata A mapping holding job's scheduling state.
 */
function setScheduledIcon(img, jobdata) {
  if (jobdata["isscheduled"]) {
    if (jobdata["hasschedule"]) {
      // The alt tag is used here to hold the isscheduled state and icon name.
      img.alt = "isactive"; 
    } else {
      img.alt = "alert";
    }
  } else {
    img.alt = "isinactive";
  }
  var activeInactive = uiData["ICONMAP"][img.alt];
  img.src = getIconPath(activeInactive[1]);
  disconnectAll(img);
  setIconMouseover(img);
  connect(img, "onclick", 
          partial(setJobScheduled, !jobdata["isscheduled"]));
}


/**
 * Button/graphic handler that tells the server to change the state of the
 * isscheduled flag on a job. This is a Mochikit event handler.
 * @param {Boolean} state The state to set the isscheduled flag to.
 * @param {Event} ev The Mochikit event.
 */
function setJobScheduled(state, ev) {
  img = ev.target()
  var d = loadJSONDoc("/plinth/jobs/scheduled/", {
                        "isscheduled": serializeJSON(state), 
                        "job_id": serializeJSON(ev.target().id.substring(4))
                      });
  d.addCallback(partial(setScheduledIcon, img));
}


/**
 * Run a TestJob via the test runner when the run icon is clicked.
 * @param {Number} jobId The job identifier (the database id) to run.
 * @param {String} jobName The name of the job.
 * @param {Event} ev The MochiKit event (this is an event handler).
 */
function runJob(jobId, jobName, ev) {
  if (window.confirm("Run '" + jobName + "'?")) {
    var d = loadJSONDoc("/testrunner/job/", {"job_ids": jobId})
    d.addCallback(partial(alertJobStart, jobName));
  }
}

/**
 * Alert the user that the requested job has started on the server.
 * @param {String} jobName The name of the job (set by server).
 * @param {Number} pid The process ID of the job on the server.
 */
function alertJobStart(jobName, pid) {
  window.alert("Started job '" + jobName + "'. Process ID: " + pid.toString());
}

/**
 * Initial setup of active icons in the jobs table.
 * @param {Element} img The image tag to check and set handlers.
 */
function setupJobsIcons(img) {
  // If id contains "job" then it is the "isscheduled" controller icon.
  if (img.id.indexOf("job") >= 0) { 
    // The server side set the initial state of alt attribute. Infer job data
    // from that and set event handlers accordingly.
    // Default to "alert" in case server didn't set it right.
    var jobdata = {"isscheduled": true, "hasschedule": false};
    if (img.alt == "isactive") {
      jobdata = {"isscheduled": true, "hasschedule": true};
    } else if (img.alt == "isinactive") {
      jobdata = {"isscheduled": false, "hasschedule": true};
    } else if (img.alt == "alert") {
      jobdata = {"isscheduled": true, "hasschedule": false};
    }
    setScheduledIcon(img, jobdata); // Set initial handlers.
  } else {
    setIconMouseover(img);
  }
}

/**
 * Handle the user selecting "submit" button. This will fetch the current
 * user job table from the django/DB and then submit it to the
 * schedmanager side.
 * @param {Event} ev The MochiKit special event object.
 */
function doSubmitJobs(ev) {
  // This is here to trigger SSO authentication.
  var da = doSimpleXMLHttpRequest("/schedule/_auth");
  wait(1);
  var d = loadJSONDoc("/plinth/jobs/get_schedule/");
  d.addCallback(submitToCrontab);
}

/**
 * POST the job data to a server update location.
 * @param {String} jobdata A string serialization (JSON) of the the user's job
 * data.
 */
function submitToCrontab(jobdata) {
  // var jobdata = evalJSONRequest(req);
  var d = doXHR("/plinth/schedule/updatecron_cb", {
                  method: "POST",
                  headers: {"Content-Type": "application/x-www-form-urlencoded"},
                  sendContent: queryString({
                    "jobdata": serializeJSON(jobdata)
                  })
//                  mimeType: "application/json"
                });
  d.addCallback(crontabSubmitDone);
}

/**
 * Alert the user if the job started on the server, or not.
 * @param {Boolean} stat True indicates job run start was successful.
 */
function crontabSubmitDone(req) {
  var stat = evalJSONRequest(req);
  if (stat) {
    window.alert("Job list successfully submitted.");
  } else {
    window.alert("Job list NOT successfully submitted. Please try again.");
  }
}

/**
 * Callback attached to delete button/icon. Calls config item delete url
 * on server.
 */
function jobDelete(jobId, jobName, ev) {
  if (window.confirm("Delete '" + jobName + "'?")) {
    var d = loadJSONDoc(jobId + "/delete/")
    d.addCallback(partial(alertJobDelete, jobName, ev.src()));
  }
}

/**
 * Callback that notifies user regarding the status of the delete
 * operation. The table row is removed on success.
 * @param {Element} img The image element that acts as a button. It's
 * parent row is the one to delete.
 * @param {String} jobName The name of the job item.
 * @param {Boolean} isSuccessful indicates if delete operation was
 * successful.
 */
function alertJobDelete(JobName, img, isSuccessful) {
  if (isSuccessful) {
    disconnectAll(img);
    var tr = getFirstParentByTagAndClassName(img, "tr");
    swapDOM(tr, null);
  } 
  else {
    window.alert("Not able to delete '" + JobName + "'.");
  }
}


/**
 * Initialize the client-side data and DOM for the jobs admin views.
 * @param {Event} ev The Mochikit event triggered by page load.
 */
function jobInit(ev) {
  forEach(document.images, setupJobsIcons);
}

