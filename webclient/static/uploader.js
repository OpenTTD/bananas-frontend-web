"use strict";

var file_list = document.querySelector("ul[id='file_list']");
var tus_url = file_list.dataset.tusUrl;
var upload_token = file_list.dataset.uploadToken;

for (let file of file_list.getElementsByTagName("li")) {
    let filename = file.dataset.filename;
    if (filename == null) continue;

    let button = file.querySelector("button");
    button.addEventListener('click', function() {
        remove_file(filename);
    });
}

var more_files = document.querySelector("li[id='more_files']");
var file_selector = document.querySelector("input[id='file_selector']");
var button_start = document.querySelector("button[id='start_upload']");
var removed_files = document.querySelector("input[id='removed_files']");
var button_validate = document.querySelector("button[id='validate']");
var button_publish = document.querySelector("button[id='publish']");
button_start.addEventListener("click", add_upload);

var upload_queue = [];
var upload_file = null;
var upload_instance = null;

function get_uuid() {
    let url = upload_instance.url;
    return url.substr(url.lastIndexOf("/") + 1);
}

function get_file(filename) {
    for (let file of file_list.getElementsByTagName("li")) {
        if (file.dataset.filename == filename) return file;
    }
    return null;
}

function remove_file(filename) {
    upload_queue = upload_queue.filter(file => file.name != filename);
    if (upload_instance != null && upload_file.name == filename) {
        upload_instance.abort();
    }
    let file = get_file(filename);
    if (file != null) {
        let uuid = file.dataset.uuid;
        if (uuid != null) {
            removed_files.value = removed_files.value.concat(",", uuid);
        }
        file.remove();
    }
}

function add_file(filename, status) {
    let new_li = document.createElement("li");
    new_li.dataset.filename = filename;
    new_li.appendChild(document.createTextNode(filename + " "));

    let new_status = document.createElement("span");
    new_status.appendChild(document.createTextNode(status));
    new_li.appendChild(new_status);
    new_li.appendChild(document.createTextNode(" "));

    let new_button = document.createElement("button");
    new_button.type = "button";
    new_button.addEventListener('click', function() {
        remove_file(filename);
    });
    new_button.appendChild(document.createTextNode("Delete file"));
    new_li.appendChild(new_button);

    file_list.insertBefore(new_li, more_files);
}

function set_file_status(filename, uuid, status) {
    let file = get_file(filename);
    if (file != null) {
        file.dataset.uuid = uuid;
        let old_status = file.querySelector("span");
        old_status.textContent = status;
    }
}

function add_upload() {
    if (file_selector.value == "") return;
    for (let i = 0; i < file_selector.files.length; i++) {
        let file = file_selector.files[i];
        if (get_file(file.name) != null) continue;
        upload_queue.push(file);
        add_file(file.name, "queued...");
    }
    file_selector.value = "";
    if (upload_instance == null) start_next_upload();
}

function start_next_upload() {
    button_validate.disabled = upload_queue.length > 0;
    button_publish.disabled = upload_queue.length > 0;
    if (upload_queue.length == 0) return;

    upload_file = upload_queue[0];
    upload_queue.shift();

    let options = {
        endpoint: tus_url,
        retryDelays: [0, 1000, 3000, 5000],
        metadata: {
            "upload-token": upload_token,
            filename: upload_file.name
        },
        onError : function(error) {
            set_file_status(upload_file.name, get_uuid(), error);
            upload_file = null;
            upload_instance = null;
            start_next_upload();
        },
        onProgress: function(bytesUploaded, bytesTotal) {
            let percentage = (bytesUploaded / bytesTotal * 100).toFixed(2);
            set_file_status(upload_file.name, get_uuid(), "uploading... " + percentage + " %");
        },
        onSuccess: function() {
            set_file_status(upload_file.name, get_uuid(), "(" + Math.floor(upload_file.size / 1024) + " kB)");
            upload_file = null;
            upload_instance = null;
            start_next_upload();
        }
    };

    upload_instance = new tus.Upload(upload_file, options);
    upload_instance.start();
}
