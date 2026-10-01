/* =========================================================
   LEARNAI COMMON JAVASCRIPT
========================================================= */

function formatNumber(value, decimals = 0) {
    const number = Number(value);

    if (Number.isNaN(number)) {
        return "0";
    }

    return number.toFixed(decimals);
}
/* =========================================================
   GET STUDENT ID
========================================================= */

function getStudentId() {

    const studentId =
        localStorage.getItem("student_id");


    if (!studentId) {

        window.location.href =
            "login.html";

        return null;
    }


    return studentId;
}


/* =========================================================
   GET USER
========================================================= */

function getCurrentUser() {

    const user =
        localStorage.getItem("user");


    if (!user) {
        return null;
    }


    try {

        return JSON.parse(user);

    } catch (error) {

        console.error(
            "Invalid user data:",
            error
        );

        return null;
    }
}


/* =========================================================
   LOGOUT
========================================================= */

function logout() {

    localStorage.removeItem(
        "user"
    );

    localStorage.removeItem(
        "student_id"
    );


    window.location.href =
        "login.html";
}


/* =========================================================
   MOBILE SIDEBAR
========================================================= */

function initializeSidebar() {

    const button =
        document.getElementById(
            "mobileMenuBtn"
        );


    const sidebar =
        document.querySelector(
            ".sidebar"
        );


    if (
        !button ||
        !sidebar
    ) {
        return;
    }


    button.addEventListener(
        "click",
        function () {

            sidebar.classList.toggle(
                "open"
            );

        }
    );


    sidebar
        .querySelectorAll("a")
        .forEach(
            function (link) {

                link.addEventListener(
                    "click",
                    function () {

                        sidebar.classList.remove(
                            "open"
                        );

                    }
                );

            }
        );
}


/* =========================================================
   LOGOUT BUTTON
========================================================= */

function initializeLogout() {

    const button =
        document.getElementById(
            "logoutBtn"
        );


    if (!button) {
        return;
    }


    button.addEventListener(
        "click",
        logout
    );
}


/* =========================================================
   ESCAPE HTML
========================================================= */

function escapeHtml(value) {

    return String(
        value ?? ""
    )
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );
}


/* =========================================================
   FORMAT TEXT
========================================================= */

function formatText(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "-";
    }


    return String(value)
        .replaceAll(
            "_",
            " "
        )
        .replace(
            /\b\w/g,
            function (letter) {

                return letter.toUpperCase();

            }
        );
}


/* =========================================================
   FORMAT PERCENTAGE
========================================================= */

function formatPercentage(value) {

    const number =
        Number(value);


    if (Number.isNaN(number)) {
        return "0%";
    }


    return `${Math.round(number)}%`;
}


/* =========================================================
   INITIALIZATION
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        initializeSidebar();

        initializeLogout();

    }
);