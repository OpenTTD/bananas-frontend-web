"use strict";

let xhr = new XMLHttpRequest();

function regionClick(event) {
    let region = event.target.dataset.region;
    let regions = document.getElementById("regions");
    regions.value += region + "\n";
}

function searchResult(regions) {
    let list = document.getElementById("region-list");
    list.innerHTML = "";

    if (regions["result"].length == 0) {
        let span = document.createElement("span");
        span.textContent = "No regions found.";
        list.appendChild(span);
        return;
    }

    for (let region of regions["result"]) {
        let li = document.createElement("li");

        li.dataset.region = region["code"];
        li.textContent = region["code"] + ": " + region["name"];

        li.addEventListener("click", regionClick);
        list.appendChild(li);
    }
}

function searchRequest() {
    let search = document.getElementById("region-search");
    let value = search.value;

    xhr.abort();

    xhr.open("GET", "/regions?search=" + encodeURIComponent(value));
    xhr.send();

    xhr.onload = function() {
        if (xhr.status != 200) {
            alert("Error: " + xhr.status + " " + xhr.statusText);
            return;
        }

        let regions = JSON.parse(xhr.responseText);
        searchResult(regions);
    };
}

document.addEventListener("DOMContentLoaded", function(event) {
    let search = document.getElementById("region-search");
    let search_timer;

    /* Search for regions when the user stops typing for 300ms. */
    search.addEventListener("input", function(event) {
        if (search_timer) {
            clearTimeout(search_timer);
        }
        search_timer = setTimeout(searchRequest, 300);
    });
});
