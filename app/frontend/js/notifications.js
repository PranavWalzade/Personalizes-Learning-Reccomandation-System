let studentId = null;

let allNotifications = [];

let currentFilter = "all";
let notificationsLoading = false;
let notificationsRefreshPending = false;


/* =========================================================
   INITIALIZATION
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    studentId = getStudentId();

    if (!studentId) {
        return;
    }

    setupEvents();

    loadProfile();

    loadNotifications();

    window.addEventListener(
        "learnai:data-changed",
        loadNotificationsAfterChange
    );

    window.addEventListener(
        "storage",
        function (event) {
            if (event.key === "learnai:data-changed") {
                loadNotificationsAfterChange();
            }
        }
    );

    window.addEventListener(
        "focus",
        loadNotificationsAfterChange
    );

    document.addEventListener(
        "visibilitychange",
        function () {
            if (!document.hidden) {
                loadNotificationsAfterChange();
            }
        }
    );

    window.setInterval(function () {
        if (!document.hidden) {
            loadNotifications(false);
        }
    }, 30000);

});


function loadNotificationsAfterChange() {
    if (!document.hidden) {
        loadNotifications(false);
    }
}


/* =========================================================
   EVENTS
   ========================================================= */

function setupEvents() {

    const refreshButton =
        document.getElementById(
            "refreshNotificationsBtn"
        );

    const markAllButton =
        document.getElementById(
            "markAllReadBtn"
        );


    if (refreshButton) {

        refreshButton.addEventListener(
            "click",
            loadNotifications
        );

    }


    if (markAllButton) {

        markAllButton.addEventListener(
            "click",
            markAllAsRead
        );

    }


    const filters =
        document.querySelectorAll(
            ".notification-filter"
        );


    filters.forEach(function (button) {

        button.addEventListener(
            "click",
            function () {

                currentFilter =
                    button.dataset.filter;

                filters.forEach(function (item) {
                    item.classList.remove("active");
                });

                button.classList.add("active");

                renderNotifications();

            }
        );

    });

}


/* =========================================================
   LOAD PROFILE
   ========================================================= */

async function loadProfile() {

    try {

        const response =
            await apiGet(
                `/profile/${studentId}`
            );


        if (!response.success) {
            return;
        }


        const profile =
            response.profile ||
            response.data ||
            {};


        const user =
            response.user ||
            profile.user ||
            {};


        const name =
            profile.student_name ||
            user.username ||
            "Student";


        document.getElementById(
            "topbarUserName"
        ).textContent = name;


        document.getElementById(
            "topbarUserBranch"
        ).textContent =
            profile.branch ||
            "Engineering";


        document.getElementById(
            "topbarAvatar"
        ).textContent =
            getInitials(name);

    } catch (error) {

        console.error(
            "Profile error:",
            error
        );

    }

}


/* =========================================================
   LOAD NOTIFICATIONS
   ========================================================= */

async function loadNotifications(showLoadingState = true) {

    if (notificationsLoading) {
        notificationsRefreshPending = true;
        return;
    }

    notificationsLoading = true;

    if (showLoadingState) {
        showLoading();
    }

    hideError();


    try {

        const response =
            await apiGet(
                `/student/${studentId}/notifications`
            );


        if (!response.success) {

            throw new Error(
                response.message ||
                "Unable to load notifications."
            );

        }


        const notifications =
            response.notifications ||
            response.data ||
            [];

        if (!Array.isArray(notifications)) {
            throw new Error(
                "Server returned an invalid notifications list."
            );
        }

        allNotifications = notifications;


        updateSummary();

        renderNotifications();

        hideLoading();


    } catch (error) {

        console.error(
            "Notifications loading error:",
            error
        );


        hideLoading();

        showError(
            error.message ||
            "Unable to load notifications."
        );

    } finally {
        notificationsLoading = false;

        if (notificationsRefreshPending) {
            notificationsRefreshPending = false;
            loadNotifications(false);
        }
    }

}


/* =========================================================
   SUMMARY
   ========================================================= */

function updateSummary() {

    const total =
        allNotifications.length;


    const unread =
        allNotifications.filter(
            function (notification) {

                return !isRead(notification);

            }
        ).length;


    const read =
        total - unread;


    document.getElementById(
        "totalNotifications"
    ).textContent = total;


    document.getElementById(
        "unreadNotifications"
    ).textContent = unread;


    document.getElementById(
        "readNotifications"
    ).textContent = read;


    const markAllButton =
        document.getElementById(
            "markAllReadBtn"
        );


    if (markAllButton) {

        markAllButton.disabled =
            unread === 0;

    }

}


/* =========================================================
   FILTER
   ========================================================= */

function getFilteredNotifications() {

    if (currentFilter === "unread") {

        return allNotifications.filter(
            function (notification) {

                return !isRead(notification);

            }
        );

    }


    if (currentFilter === "read") {

        return allNotifications.filter(
            function (notification) {

                return isRead(notification);

            }
        );

    }


    return allNotifications;

}


/* =========================================================
   RENDER
   ========================================================= */

function renderNotifications() {

    const container =
        document.getElementById(
            "notificationsContainer"
        );


    const emptyState =
        document.getElementById(
            "emptyState"
        );


    const notifications =
        getFilteredNotifications();


    if (!notifications.length) {

        container.style.display = "none";

        emptyState.style.display = "block";

        return;

    }


    emptyState.style.display = "none";

    container.style.display = "flex";


    container.innerHTML =
        notifications.map(
            function (notification) {

                return createNotificationHTML(
                    notification
                );

            }
        ).join("");


    attachNotificationEvents();

}


/* =========================================================
   CREATE CARD
   ========================================================= */

function createNotificationHTML(notification) {

    const id =
        notification.id;


    const title =
        notification.title ||
        "Notification";


    const message =
        notification.message ||
        "";


    const type =
        notification.notification_type ||
        notification.type ||
        "info";


    const read =
        isRead(notification);


    const createdAt =
        notification.created_at ||
        "";


    const icon =
        getNotificationIcon(type);


    return `

        <div
            class="notification-card ${read ? "read" : "unread"}"
            data-id="${escapeHtml(id)}"
        >

            <div class="notification-icon">
                ${icon}
            </div>


            <div class="notification-content">

                <div class="notification-title-row">

                    <h3 class="notification-title">
                        ${escapeHtml(title)}
                    </h3>

                    <span class="notification-type">
                        ${escapeHtml(
                            formatText(type)
                        )}
                    </span>

                </div>


                <p class="notification-message">
                    ${escapeHtml(message)}
                </p>


                <div class="notification-time">
                    ${formatNotificationDate(createdAt)}
                </div>

            </div>


            <div class="notification-action">

                ${
                    !read
                    ? `
                        <button
                            class="mark-read-btn"
                            data-id="${escapeHtml(id)}"
                            type="button"
                        >
                            Mark read
                        </button>
                    `
                    : `
                        <span class="notification-type">
                            Read
                        </span>
                    `
                }

            </div>

        </div>

    `;

}


/* =========================================================
   EVENTS ON CARDS
   ========================================================= */

function attachNotificationEvents() {

    const buttons =
        document.querySelectorAll(
            ".mark-read-btn"
        );


    buttons.forEach(function (button) {

        button.addEventListener(
            "click",
            function (event) {

                event.stopPropagation();

                const id =
                    button.dataset.id;

                markAsRead(id);

            }
        );

    });


    const cards =
        document.querySelectorAll(
            ".notification-card.unread"
        );


    cards.forEach(function (card) {

        card.addEventListener(
            "click",
            function () {

                const id =
                    card.dataset.id;

                markAsRead(id);

            }
        );

    });

}


/* =========================================================
   MARK ONE READ
   ========================================================= */

async function markAsRead(notificationId) {

    try {

        const response =
            await apiPut(
                `/student/${studentId}/notifications/${notificationId}/read`,
                {}
            );


        if (!response.success) {

            throw new Error(
                response.message ||
                "Unable to mark notification as read."
            );

        }


        /*
         * Update local data immediately.
         */

        allNotifications =
            allNotifications.map(
                function (notification) {

                    if (
                        String(notification.id) ===
                        String(notificationId)
                    ) {

                        return {
                            ...notification,
                            is_read: 1
                        };

                    }

                    return notification;

                }
            );


        updateSummary();

        renderNotifications();


    } catch (error) {

        console.error(
            "Mark read error:",
            error
        );

        showError(
            error.message ||
            "Unable to mark notification as read."
        );

    }

}


/* =========================================================
   MARK ALL READ
   ========================================================= */

async function markAllAsRead() {

    const unread =
        allNotifications.filter(
            function (notification) {
                return !isRead(notification);
            }
        );


    if (!unread.length) {
        return;
    }


    const button =
        document.getElementById(
            "markAllReadBtn"
        );


    button.disabled = true;

    button.dataset.originalText =
        button.textContent;

    button.textContent =
        "Updating...";


    try {

        const response = await apiPut(
            `/student/${studentId}/notifications/read-all`,
            {}
        );

        if (!response.success) {
            throw new Error(
                response.message ||
                "Unable to mark all notifications as read."
            );
        }

        allNotifications =
            allNotifications.map(
                function (notification) {

                    return {
                        ...notification,
                        is_read: 1
                    };

                }
            );


        updateSummary();

        renderNotifications();


    } catch (error) {

        console.error(
            "Mark all read error:",
            error
        );


        showError(
            error.message ||
            "Unable to mark all notifications as read."
        );

    } finally {

        button.disabled =
            allNotifications.every(isRead);

        button.textContent =
            button.dataset.originalText ||
            "✓ Mark All as Read";

    }

}


/* =========================================================
   READ CHECK
   ========================================================= */

function isRead(notification) {

    return (
        notification.is_read === true ||
        notification.is_read === 1 ||
        notification.is_read === "1"
    );

}


/* =========================================================
   ICON
   ========================================================= */

function getNotificationIcon(type) {

    const value =
        String(type || "").toLowerCase();


    if (value.includes("recommend")) {
        return "✦";
    }


    if (value.includes("skill")) {
        return "◈";
    }


    if (value.includes("course")) {
        return "📚";
    }


    if (value.includes("progress")) {
        return "📈";
    }


    if (value.includes("success")) {
        return "✓";
    }


    if (value.includes("warning")) {
        return "⚠";
    }


    return "🔔";

}


/* =========================================================
   DATE FORMAT
   ========================================================= */

function formatNotificationDate(value) {

    if (!value) {
        return "-";
    }


    const date =
        new Date(value);


    if (Number.isNaN(date.getTime())) {
        return escapeHtml(value);
    }


    return date.toLocaleString(
        "en-IN",
        {
            day: "numeric",
            month: "short",
            year: "numeric",
            hour: "numeric",
            minute: "2-digit"
        }
    );

}


/* =========================================================
   HELPERS
   ========================================================= */

function showLoading() {

    document.getElementById(
        "loading"
    ).style.display = "flex";


    document.getElementById(
        "notificationsContainer"
    ).style.display = "none";


    document.getElementById(
        "emptyState"
    ).style.display = "none";

}


function hideLoading() {

    document.getElementById(
        "loading"
    ).style.display = "none";

}


function showError(message) {

    const element =
        document.getElementById(
            "errorMessage"
        );


    element.textContent = message;

    element.style.display = "block";

}


function hideError() {

    document.getElementById(
        "errorMessage"
    ).style.display = "none";

}


function getInitials(name) {

    if (!name) {
        return "ST";
    }


    const parts =
        String(name)
            .trim()
            .split(/\s+/);


    if (parts.length === 1) {

        return parts[0]
            .substring(0, 2)
            .toUpperCase();

    }


    return (
        parts[0][0] +
        parts[parts.length - 1][0]
    ).toUpperCase();

}