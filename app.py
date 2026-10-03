// ======================================================

// SMARTCLASS RESPONSE API

// ======================================================



const SPREADSHEET = SpreadsheetApp.getActiveSpreadsheet();



const ACTIVITIES_SHEET = "Activities";

const RESPONSES_SHEET = "Responses";
const VOTES_SHEET = "Votes";



// ======================================================

// GOOGLE DRIVE ROOT FOLDER

// ======================================================



const ROOT_FOLDER_ID = "1yech9R7MMbMY9fIZM_FUrODiO8z62Ng1";



// Upload limits (bytes)

const MAX_DOCUMENT_BYTES = 5 * 1024 * 1024;

const MAX_IMAGE_BYTES = 5 * 1024 * 1024;

const MAX_VIDEO_BYTES = 8 * 1024 * 1024;

const MAX_TOTAL_UPLOAD_BYTES = 12 * 1024 * 1024;

const MAX_ATTACHMENTS = 5;



// ======================================================

// GET REQUESTS

// ======================================================



function doGet(e) {

  try {

    const action = e.parameter.action;



    if (action === "get_activity") {

      const sessionId = e.parameter.session_id;

      return jsonResponse(getActivity(sessionId));

    }



    if (action === "get_activities") {

      return jsonResponse(getAllActivities());

    }



    if (action === "get_responses") {

      const sessionId = e.parameter.session_id;

      return jsonResponse(getResponses(sessionId));

    }



    return jsonResponse({

      success: true,

      message: "SmartClass API is running."

    });



  } catch (error) {

    return jsonResponse({

      success: false,

      error: error.toString()

    });

  }

}



// ======================================================

// POST REQUESTS

// ======================================================



function doPost(e) {

  try {

    const data = JSON.parse(e.postData.contents);

    const action = data.action;



    if (action === "create_activity") {

      return jsonResponse(createActivity(data));

    }



    if (action === "submit_response") {

      return jsonResponse(submitResponse(data));

    }



    return jsonResponse({

      success: false,

      error: "Unknown action."

    });



  } catch (error) {

    return jsonResponse({

      success: false,

      error: error.toString()

    });

  }

}



// ======================================================

// CREATE ACTIVITY

// ======================================================



function createActivity(data) {

  const sheet = SPREADSHEET.getSheetByName(ACTIVITIES_SHEET);



  if (!sheet) {

    throw new Error("Activities sheet was not found.");

  }



  const existing = findActivityRow(data.session_id);



  if (existing !== -1) {

    return {

      success: false,

      error: "Session ID already exists."

    };

  }



  const folderInfo = createActivityFolders(

    data.course,

    data.semester,

    data.session_id,

    data.created_date

  );



  sheet.appendRow([

    data.session_id,

    data.course,

    data.semester,

    data.activity_title,

    data.question,

    data.instructions || "",

    data.created_date,

    data.created_time,

    data.allow_email,

    data.allow_document,

    data.allow_image,

    data.allow_video,

    "Active",

    "", // Instructor_File_Name

    "", // Instructor_File_Type

    "", // Instructor_File_URL

    folderInfo.activityFolderUrl

  ]);



  return {

    success: true,

    message: "Activity created successfully.",

    session_id: data.session_id,

    folder_url: folderInfo.activityFolderUrl

  };

}



// ======================================================

// FIND ACTIVITY ROW

// ======================================================



function findActivityRow(sessionId) {

  const sheet = SPREADSHEET.getSheetByName(ACTIVITIES_SHEET);



  if (!sheet) {

    return -1;

  }



  const values = sheet.getDataRange().getValues();



  for (let i = 1; i < values.length; i++) {

    if (

      String(values[i][0]).trim() ===

      String(sessionId).trim()

    ) {

      return i + 1;

    }

  }



  return -1;

}



// ======================================================

// GET ONE ACTIVITY

// ======================================================



function getActivity(sessionId) {

  if (!sessionId) {

    return {

      success: false,

      error: "Session ID is required."

    };

  }



  const sheet = SPREADSHEET.getSheetByName(ACTIVITIES_SHEET);



  if (!sheet) {

    return {

      success: false,

      error: "Activities sheet was not found."

    };

  }



  const values = sheet.getDataRange().getValues();



  for (let i = 1; i < values.length; i++) {

    if (

      String(values[i][0]).trim() ===

      String(sessionId).trim()

    ) {

      return {

        success: true,

        activity: activityObjectFromRow(values[i])

      };

    }

  }



  return {

    success: false,

    error: "Activity/session was not found."

  };

}



// ======================================================

// GET ALL ACTIVITIES

// ======================================================



function getAllActivities() {

  const sheet = SPREADSHEET.getSheetByName(ACTIVITIES_SHEET);



  if (!sheet) {

    return {

      success: false,

      error: "Activities sheet was not found."

    };

  }



  const values = sheet.getDataRange().getValues();

  const activities = [];



  for (let i = 1; i < values.length; i++) {

    if (!values[i][0]) {

      continue;

    }



    activities.push(activityObjectFromRow(values[i]));

  }



  activities.reverse();



  return {

    success: true,

    count: activities.length,

    activities: activities

  };

}



function activityObjectFromRow(row) {

  return {

    session_id: row[0],

    course: row[1],

    semester: row[2],

    activity_title: row[3],

    question: row[4],

    instructions: row[5],

    created_date: row[6],

    created_time: row[7],

    allow_email: row[8],

    allow_document: row[9],

    allow_image: row[10],

    allow_video: row[11],

    status: row[12],

    instructor_file_name: row[13],

    instructor_file_type: row[14],

    instructor_file_url: row[15],

    drive_folder_url: row[16]

  };

}



// ======================================================

// SUBMIT STUDENT RESPONSE + ATTACHMENTS

// ======================================================



function submitResponse(data) {

  const responseSheet = SPREADSHEET.getSheetByName(RESPONSES_SHEET);



  if (!responseSheet) {

    throw new Error("Responses sheet was not found.");

  }



  const activityRowNumber = findActivityRow(data.session_id);



  if (activityRowNumber === -1) {

    return {

      success: false,

      error: "Invalid classroom session."

    };

  }



  if (!data.answer || String(data.answer).trim() === "") {

    return {

      success: false,

      error: "Student answer is required."

    };

  }



  const activitySheet = SPREADSHEET.getSheetByName(ACTIVITIES_SHEET);

  const activityRow = activitySheet

    .getRange(activityRowNumber, 1, 1, 18)

    .getValues()[0];



  const activity = activityObjectFromRow(activityRow);



  if (String(activity.status).trim().toLowerCase() !== "active") {

    return {

      success: false,

      error: "This classroom activity is closed."

    };

  }



  const attachments = Array.isArray(data.attachments)

    ? data.attachments

    : [];



  const validation = validateAttachments(attachments, activity);



  if (!validation.success) {

    return validation;

  }



  const responseId = Utilities.getUuid();



  // Save files only after every attachment has passed validation.

  const savedAttachments = saveStudentAttachments(

    attachments,

    activity,

    responseId

  );



  const attachmentTypes = savedAttachments.map(function(item) {

    return item.type;

  });



  const attachmentNames = savedAttachments.map(function(item) {

    return item.name;

  });



  const attachmentUrls = savedAttachments.map(function(item) {

    return item.url;

  });



  // Existing three attachment columns are kept.

  // For multiple files, each cell stores a JSON array.

  responseSheet.appendRow([

    responseId,

    data.session_id,

    data.submitted_date,

    data.submitted_time,

    data.student_email || "",

    String(data.answer).trim(),

    savedAttachments.length ? JSON.stringify(attachmentTypes) : "",

    savedAttachments.length ? JSON.stringify(attachmentNames) : "",

    savedAttachments.length ? JSON.stringify(attachmentUrls) : ""

  ]);



  return {

    success: true,

    message: "Response submitted successfully.",

    response_id: responseId,

    attachment_count: savedAttachments.length,

    attachments: savedAttachments

  };

}



// ======================================================

// VALIDATE STUDENT ATTACHMENTS

// ======================================================



function validateAttachments(attachments, activity) {

  if (attachments.length > MAX_ATTACHMENTS) {

    return {

      success: false,

      error: "A maximum of " + MAX_ATTACHMENTS + " attachments is allowed."

    };

  }



  let totalBytes = 0;



  for (let i = 0; i < attachments.length; i++) {

    const item = attachments[i] || {};

    const category = String(item.category || "").toLowerCase().trim();

    const fileName = String(item.name || "").trim();

    const mimeType = String(item.mime_type || "application/octet-stream").trim();

    const base64Data = String(item.base64 || "").trim();



    if (!fileName || !base64Data) {

      return {

        success: false,

        error: "One of the uploaded files is incomplete."

      };

    }



    if (["document", "image", "video"].indexOf(category) === -1) {

      return {

        success: false,

        error: "Unsupported attachment category."

      };

    }



    if (category === "document" && !isTruthy(activity.allow_document)) {

      return {

        success: false,

        error: "Document uploads are not enabled for this activity."

      };

    }



    if (category === "image" && !isTruthy(activity.allow_image)) {

      return {

        success: false,

        error: "Image uploads are not enabled for this activity."

      };

    }



    if (category === "video" && !isTruthy(activity.allow_video)) {

      return {

        success: false,

        error: "Video uploads are not enabled for this activity."

      };

    }



    if (!isAllowedFile(category, fileName, mimeType)) {

      return {

        success: false,

        error: "File type is not allowed: " + fileName

      };

    }



    let bytes;



    try {

      bytes = Utilities.base64Decode(base64Data);

    } catch (error) {

      return {

        success: false,

        error: "Could not read uploaded file: " + fileName

      };

    }



    const fileSize = bytes.length;

    totalBytes += fileSize;



    if (category === "document" && fileSize > MAX_DOCUMENT_BYTES) {

      return {

        success: false,

        error: "Document is too large: " + fileName + ". Maximum size is 5 MB."

      };

    }



    if (category === "image" && fileSize > MAX_IMAGE_BYTES) {

      return {

        success: false,

        error: "Image is too large: " + fileName + ". Maximum size is 5 MB."

      };

    }



    if (category === "video" && fileSize > MAX_VIDEO_BYTES) {

      return {

        success: false,

        error: "Video is too large: " + fileName + ". Maximum size is 8 MB."

      };

    }

  }



  if (totalBytes > MAX_TOTAL_UPLOAD_BYTES) {

    return {

      success: false,

      error: "The combined attachment size is too large. Maximum total size is 12 MB."

    };

  }



  return {

    success: true

  };

}



function isAllowedFile(category, fileName, mimeType) {

  const extension = getFileExtension(fileName);

  const mime = String(mimeType || "").toLowerCase();



  const documentExtensions = [

    "pdf", "doc", "docx", "ppt", "pptx",

    "xls", "xlsx", "txt", "csv"

  ];



  const imageExtensions = [

    "jpg", "jpeg", "png", "webp"

  ];



  const videoExtensions = [

    "mp4", "mov", "webm"

  ];



  if (category === "document") {

    return documentExtensions.indexOf(extension) !== -1;

  }



  if (category === "image") {

    return (

      imageExtensions.indexOf(extension) !== -1 &&

      (mime.indexOf("image/") === 0 || mime === "application/octet-stream")

    );

  }



  if (category === "video") {

    return (

      videoExtensions.indexOf(extension) !== -1 &&

      (mime.indexOf("video/") === 0 || mime === "application/octet-stream")

    );

  }



  return false;

}



function getFileExtension(fileName) {

  const parts = String(fileName).toLowerCase().split(".");

  return parts.length > 1 ? parts.pop() : "";

}



function isTruthy(value) {

  return value === true || String(value).toLowerCase() === "true";

}



// ======================================================

// SAVE STUDENT ATTACHMENTS TO GOOGLE DRIVE

// ======================================================



function saveStudentAttachments(attachments, activity, responseId) {

  if (!attachments || attachments.length === 0) {

    return [];

  }



  const activityFolder = getFolderFromUrl(activity.drive_folder_url);

  const studentUploadsFolder = getOrCreateFolder(

    activityFolder,

    "Student Uploads"

  );



  const saved = [];



  for (let i = 0; i < attachments.length; i++) {

    const item = attachments[i];

    const category = String(item.category).toLowerCase().trim();

    const originalName = cleanFileName(item.name);

    const mimeType = String(item.mime_type || "application/octet-stream");

    const bytes = Utilities.base64Decode(String(item.base64));



    let folderName = "Documents";



    if (category === "image") {

      folderName = "Images";

    } else if (category === "video") {

      folderName = "Videos";

    }



    const destinationFolder = getOrCreateFolder(

      studentUploadsFolder,

      folderName

    );



    const storedName = cleanFileName(

      responseId.substring(0, 8) + "_" + originalName

    );



    const blob = Utilities.newBlob(

      bytes,

      mimeType,

      storedName

    );



    const driveFile = destinationFolder.createFile(blob);



    saved.push({

      type: category,

      name: originalName,

      stored_name: storedName,

      mime_type: mimeType,

      url: driveFile.getUrl(),

      file_id: driveFile.getId()

    });

  }



  return saved;

}



function getFolderFromUrl(folderUrl) {

  const url = String(folderUrl || "").trim();



  if (!url) {

    throw new Error("Activity Google Drive folder was not found.");

  }



  let match = url.match(/\\/folders\\/([a-zA-Z0-9_-]+)/);



  if (!match) {

    match = url.match(/[-\w]{20,}/);

  }



  if (!match) {

    throw new Error("Could not identify the activity Google Drive folder.");

  }



  const folderId = match[1] || match[0];

  return DriveApp.getFolderById(folderId);

}



function cleanFileName(name) {

  const cleaned = String(name || "file")

    .replace(/[\\/\\\\:*?"<>|]/g, "-")

    .replace(/[\r\n\t]/g, " ")

    .trim();



  return cleaned || "file";

}



// ======================================================

// GET STUDENT RESPONSES FOR ONE ACTIVITY

// ======================================================



function getResponses(sessionId) {

  if (!sessionId) {

    return {

      success: false,

      error: "Session ID is required.",

      responses: []

    };

  }



  const activityRow = findActivityRow(sessionId);



  if (activityRow === -1) {

    return {

      success: false,

      error: "Activity/session was not found.",

      responses: []

    };

  }



  const sheet = SPREADSHEET.getSheetByName(RESPONSES_SHEET);



  if (!sheet) {

    return {

      success: false,

      error: "Responses sheet was not found.",

      responses: []

    };

  }



  const values = sheet.getDataRange().getValues();

  const responses = [];



  for (let i = 1; i < values.length; i++) {

    const rowSessionId = String(values[i][1]).trim();



    if (rowSessionId === String(sessionId).trim()) {

      responses.push({

        response_id: values[i][0],

        session_id: values[i][1],

        submitted_date: values[i][2],

        submitted_time: values[i][3],

        student_email: values[i][4],

        answer: values[i][5],

        attachment_type: values[i][6],

        attachment_name: values[i][7],

        attachment_url: values[i][8],

        attachments: buildAttachmentObjects(

          values[i][6],

          values[i][7],

          values[i][8]

        )

      });

    }

  }



  responses.reverse();



  return {

    success: true,

    count: responses.length,

    responses: responses

  };

}



function buildAttachmentObjects(typeCell, nameCell, urlCell) {

  const types = parseStoredArray(typeCell);

  const names = parseStoredArray(nameCell);

  const urls = parseStoredArray(urlCell);



  const count = Math.max(types.length, names.length, urls.length);

  const attachments = [];



  for (let i = 0; i < count; i++) {

    attachments.push({

      type: types[i] || "file",

      name: names[i] || "Attachment",

      url: urls[i] || ""

    });

  }



  return attachments;

}



function parseStoredArray(value) {

  if (value === null || value === undefined || String(value).trim() === "") {

    return [];

  }



  const text = String(value).trim();



  try {

    const parsed = JSON.parse(text);

    return Array.isArray(parsed) ? parsed : [text];

  } catch (error) {

    // Backward compatibility with any older single-file response.

    return [text];

  }

}




// ======================================================
// STUDENT VOTING
// ======================================================

function normalizeVotingStatus(value) {
  const text = String(value || "").trim().toLowerCase();
  if (text === "open") return "Open";
  if (text === "closed") return "Closed";
  return "Not Started";
}

function setVotingStatus(data) {
  const sessionId = String(data.session_id || "").trim();
  const status = normalizeVotingStatus(data.status);
  if (!sessionId) return {success:false,error:"Session ID is required."};
  const row = findActivityRow(sessionId);
  if (row === -1) return {success:false,error:"Activity/session was not found."};
  SPREADSHEET.getSheetByName(ACTIVITIES_SHEET).getRange(row,18).setValue(status);
  return {success:true,session_id:sessionId,voting_status:status,message:"Voting status updated successfully."};
}

function getVoting(sessionId) {
  const a=getActivity(sessionId);
  if (!a.success) return {success:false,error:a.error,responses:[]};
  const status=normalizeVotingStatus(a.activity.voting_status);
  if (status!=="Open") return {success:false,error:status==="Closed"?"Voting is closed.":"Voting has not started.",voting_status:status,responses:[]};
  const r=getResponses(sessionId);
  if (!r.success) return r;
  const responses=r.responses.map(function(x){return {response_id:x.response_id,answer:x.answer};});
  return {success:true,session_id:sessionId,activity_title:a.activity.activity_title,question:a.activity.question,voting_status:status,count:responses.length,responses:responses};
}

function submitVote(data) {
  const sid=String(data.session_id||"").trim(), rid=String(data.response_id||"").trim(), vid=String(data.voter_id||"").trim();
  if (!sid||!rid||!vid) return {success:false,error:"Session ID, response ID and voter ID are required."};
  const a=getActivity(sid);
  if (!a.success) return {success:false,error:a.error};
  if (normalizeVotingStatus(a.activity.voting_status)!=="Open") return {success:false,error:"Voting is not open for this activity."};
  const r=getResponses(sid);
  if (!r.success) return {success:false,error:r.error};
  if (!r.responses.some(function(x){return String(x.response_id).trim()===rid;})) return {success:false,error:"The selected answer does not belong to this activity."};
  const sheet=SPREADSHEET.getSheetByName(VOTES_SHEET);
  if (!sheet) return {success:false,error:"Votes sheet was not found."};
  const vals=sheet.getDataRange().getValues();
  for(let i=1;i<vals.length;i++) if(String(vals[i][1]||"").trim()===sid && String(vals[i][3]||"").trim()===vid) return {success:false,error:"You have already voted in this activity."};
  const id=Utilities.getUuid(), now=new Date(), tz=Session.getScriptTimeZone();
  sheet.appendRow([id,sid,rid,vid,data.vote_date||Utilities.formatDate(now,tz,"dd MMMM yyyy"),data.vote_time||Utilities.formatDate(now,tz,"HH:mm:ss")]);
  return {success:true,message:"Your vote has been recorded.",vote_id:id};
}

function getVoteResults(sessionId) {
  const sid=String(sessionId||"").trim();
  if(!sid) return {success:false,error:"Session ID is required.",results:[]};
  const a=getActivity(sid), r=getResponses(sid);
  if(!a.success) return {success:false,error:a.error,results:[]};
  if(!r.success) return {success:false,error:r.error,results:[]};
  const sheet=SPREADSHEET.getSheetByName(VOTES_SHEET);
  if(!sheet) return {success:false,error:"Votes sheet was not found.",results:[]};
  const counts={}, vals=sheet.getDataRange().getValues(); let total=0;
  for(let i=1;i<vals.length;i++) if(String(vals[i][1]||"").trim()===sid){const id=String(vals[i][2]||"").trim();counts[id]=(counts[id]||0)+1;total++;}
  const results=r.responses.map(function(x){return {response_id:x.response_id,answer:x.answer,votes:counts[String(x.response_id).trim()]||0};});
  results.sort(function(a,b){return b.votes-a.votes;});
  let prev=null,rank=0;
  for(let i=0;i<results.length;i++){if(prev===null||results[i].votes<prev)rank=i+1;results[i].rank=rank;prev=results[i].votes;}
  return {success:true,session_id:sid,voting_status:normalizeVotingStatus(a.activity.voting_status),total_votes:total,results:results};
}

// ======================================================

// CREATE GOOGLE DRIVE STRUCTURE

// ======================================================



function createActivityFolders(course, semester, sessionId, date) {

  const root = DriveApp.getFolderById(ROOT_FOLDER_ID);



  const courseFolder = getOrCreateFolder(

    root,

    cleanFolderName(course)

  );



  const semesterFolder = getOrCreateFolder(

    courseFolder,

    cleanFolderName(semester)

  );



  const activityFolderName = cleanFolderName(

    date + "_" + sessionId

  );



  const activityFolder = getOrCreateFolder(

    semesterFolder,

    activityFolderName

  );



  getOrCreateFolder(

    activityFolder,

    "Instructor Files"

  );



  const studentFolder = getOrCreateFolder(

    activityFolder,

    "Student Uploads"

  );



  getOrCreateFolder(studentFolder, "Images");

  getOrCreateFolder(studentFolder, "Documents");

  getOrCreateFolder(studentFolder, "Videos");



  return {

    activityFolderId: activityFolder.getId(),

    activityFolderUrl: activityFolder.getUrl()

  };

}



// ======================================================

// GET OR CREATE GOOGLE DRIVE FOLDER

// ======================================================



function getOrCreateFolder(parent, folderName) {

  const folders = parent.getFoldersByName(folderName);



  if (folders.hasNext()) {

    return folders.next();

  }



  return parent.createFolder(folderName);

}



// ======================================================

// CLEAN DRIVE FOLDER NAME

// ======================================================



function cleanFolderName(name) {

  return String(name)

    .replace(/[\\/\\\\:*?"<>|]/g, "-")

    .trim();

}



// ======================================================

// JSON RESPONSE

// ======================================================



function jsonResponse(data) {

  return ContentService

    .createTextOutput(JSON.stringify(data))

    .setMimeType(ContentService.MimeType.JSON);

}




