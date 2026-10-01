/* =========================================================
   LEARNAI API
========================================================= */

const API_BASE_URL =
    "http://127.0.0.1:5000/api";


async function apiRequest(
    endpoint,
    options = {}
) {

    const config = {
        method: options.method || "GET",

        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    };


    if (options.body !== undefined) {

        config.body =
            typeof options.body === "string"
                ? options.body
                : JSON.stringify(options.body);
    }


    let response;

    try {
        response = await fetch(
            `${API_BASE_URL}${endpoint}`,
            config
        );
    } catch (error) {
        throw new Error(
            "Unable to connect to LearnAI. Start the backend server and try again."
        );
    }


    let data = null;


    try {

        data = await response.json();

    } catch (error) {

        throw new Error(
            "Server returned an invalid response."
        );
    }


    if (!response.ok) {

        throw new Error(
            data.message ||
            data.error ||
            `Request failed (${response.status})`
        );
    }

    if (config.method !== "GET") {
        announceDataChange(endpoint, config.method);
    }

    return data;
}


function announceDataChange(endpoint, method) {
    const change = {
        endpoint: endpoint,
        method: method,
        changedAt: Date.now()
    };

    window.dispatchEvent(
        new CustomEvent("learnai:data-changed", {
            detail: change
        })
    );

    try {
        localStorage.setItem(
            "learnai:data-changed",
            JSON.stringify(change)
        );
    } catch (error) {
        console.warn(
            "Unable to notify other tabs about the update:",
            error
        );
    }
}


/* =========================================================
   GET
========================================================= */

async function apiGet(endpoint) {

    return await apiRequest(
        endpoint,
        {
            method: "GET"
        }
    );
}


/* =========================================================
   POST
========================================================= */

async function apiPost(
    endpoint,
    body = {}
) {

    return await apiRequest(
        endpoint,
        {
            method: "POST",
            body: body
        }
    );
}


/* =========================================================
   PUT
========================================================= */

async function apiPut(endpoint, body) {
    return await apiRequest(
        endpoint,
        {
            method: "PUT",
            body: body
        }
    );
}


/* =========================================================
   DELETE
========================================================= */

async function apiDelete(endpoint) {

    return await apiRequest(
        endpoint,
        {
            method: "DELETE"
        }
    );
}