"use strict";

function capitalize(value)
{
    return value[0].toUpperCase() + value.slice(1);
}

function titleCase(str) {
    return str.replace(
        /\w+/g,
        capitalize
    );
}

function filterList() {
    let list = document.getElementById("bananas-table");

    for (var i = 0; i < list.rows.length; i++) {
        let row = list.rows[i];

        /* Skip the header. */
        if (i == 0) continue;

        /* For all filters, check if this entry is a match. */
        let match = true;
        let filters = document.getElementsByClassName("filter-select");
        for (let filter of filters) {
            let value = row.dataset[filter.name];

            if (filter.value != "" && value != filter.value) {
                match = false;
                break;
            }
        }

        row.style.display = match ? "" : "none";
    }

    /* Update the query-string with the current selected filters. */
    let params = new URLSearchParams();
    let filters = document.getElementsByClassName("filter-select");
    for (let filter of filters) {
        if (filter.value != "") {
            params.append(filter.name, filter.value);
        } else {
            params.delete(filter.name);
        }
    }
    window.history.replaceState({}, "", "?" + params.toString());
}

document.addEventListener("DOMContentLoaded", function(event) {
    /* Find all types of classifications and their options. */
    let classifications = new Map();
    let list = document.getElementById("bananas-table");
    for (var i = 0; i < list.rows.length; i++) {
        let row = list.rows[i];
        for (let key in row.dataset) {
            let value = row.dataset[key];

            if (classifications.has(key)) {
                classifications.get(key).add(value);
            } else {
                classifications.set(key, new Set([value]));
            }
        }
    }

    /* By default the filter is hidden; only show if the Javascript is loaded and there is at least one classification. */
    if (classifications.size == 0) return;

    /* For each classification, create a filter. */
    let filter = document.getElementById("filter-anchor");
    for (let classification of classifications) {
        let div = document.createElement("div");

        let label = document.createElement("label");
        label.for = "filter-" + classification[0];
        label.textContent = titleCase(classification[0]);
        div.appendChild(label);

        let select = document.createElement("select");
        select.id = "filter-" + classification[0];
        select.name = classification[0];
        select.className = "filter-select";
        select.addEventListener("input", filterList);

        let option = document.createElement("option");
        option.value = "";
        option.text = "All";
        select.appendChild(option);

        for (let value of Array.from(classification[1]).sort()) {
            let disply_value = value;

            /* Replace "-" with a space. */
            disply_value = disply_value.replace(/-/g, " ");
            /* Capitalize the first letter of each word. */
            disply_value = titleCase(disply_value);

            let option = document.createElement("option");
            option.value = value;
            option.text = disply_value;
            select.appendChild(option);
        }

        div.appendChild(select);
        filter.appendChild(div);
    }

    document.getElementById("filter-anchor").style.display = "block";

    /* Read the query-string and set the filter accordingly. */
    let params = new URLSearchParams(window.location.search);
    for (let param of params) {
        let select = document.getElementById("filter-" + param[0]);
        if (select) {
            select.value = param[1];
        }
    }

    /* Apply the filter. */
    filterList();
});
