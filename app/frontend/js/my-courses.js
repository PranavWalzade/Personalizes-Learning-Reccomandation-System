/* =========================================================
   LEARNAI - MY COURSES
========================================================= */

let allCourses = [];

let studentId = null;


/* =========================================================
   INITIALIZE
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        studentId = getStudentId();

        if (!studentId) {
            return;
        }

        initializePage();

    }
);


/* =========================================================
   PAGE INITIALIZATION
========================================================= */

async function initializePage() {

    try {

        await loadProfile();

        await loadCourses();

        initializeFilters();

    } catch (error) {

        console.error(
            "Page initialization error:",
            error
        );

        showPageMessage(
            "Unable to load your courses.",
            "error"
        );

    }

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

        if (
            !response ||
            !response.success ||
            !response.profile
        ) {
            return;
        }

        const profile =
            response.profile;

        const name =
            profile.student_name ||
            profile.username ||
            "Student";

        const branch =
            profile.branch ||
            "Engineering Student";

        const nameElement =
            document.getElementById(
                "topbarName"
            );

        const branchElement =
            document.getElementById(
                "topbarBranch"
            );

        const avatarElement =
            document.getElementById(
                "topbarAvatar"
            );

        if (nameElement) {
            nameElement.textContent = name;
        }

        if (branchElement) {
            branchElement.textContent = branch;
        }

        if (avatarElement) {
            avatarElement.textContent =
                getInitials(name);
        }

    } catch (error) {

        console.error(
            "Profile loading error:",
            error
        );

    }

}


/* =========================================================
   GET INITIALS
========================================================= */

function getInitials(name) {

    if (!name) {
        return "S";
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


/* =========================================================
   LOAD COURSES
========================================================= */

async function loadCourses() {

    showLoading(true);

    try {

        const response =
            await apiGet(
                `/student/${studentId}/courses`
            );

        console.log(
            "My courses response:",
            response
        );

        if (
            !response ||
            !response.success
        ) {

            throw new Error(
                response?.message ||
                "Unable to load courses."
            );

        }

        allCourses =
            Array.isArray(
                response.courses
            )
                ? response.courses
                : [];

        updateSummary();

        renderCourses();

    } catch (error) {

        console.error(
            "Courses loading error:",
            error
        );

        allCourses = [];

        updateSummary();

        const container =
            document.getElementById(
                "coursesContainer"
            );

        const emptyState =
            document.getElementById(
                "emptyState"
            );

        const countText =
            document.getElementById(
                "courseCountText"
            );

        if (container) {
            container.innerHTML = "";
        }

        if (emptyState) {
            emptyState.style.display =
                "block";
        }

        if (countText) {
            countText.textContent =
                "Unable to load courses.";
        }

        showPageMessage(
            error.message ||
            "Unable to load courses.",
            "error"
        );

    } finally {

        showLoading(false);

    }

}


/* =========================================================
   SUMMARY
========================================================= */

function updateSummary() {

    const total =
        allCourses.length;

    const inProgress =
        allCourses.filter(
            function (course) {

                return normalizeStatus(
                    course.status
                ) === "in_progress";

            }
        ).length;

    const completed =
        allCourses.filter(
            function (course) {

                return normalizeStatus(
                    course.status
                ) === "completed";

            }
        ).length;

    let totalProgress = 0;

    allCourses.forEach(
        function (course) {

            totalProgress +=
                getProgress(course);

        }
    );

    const averageProgress =
        total > 0
            ? Math.round(
                totalProgress / total
            )
            : 0;

    const totalElement =
        document.getElementById(
            "totalCourses"
        );

    const progressElement =
        document.getElementById(
            "inProgressCourses"
        );

    const completedElement =
        document.getElementById(
            "completedCourses"
        );

    const averageElement =
        document.getElementById(
            "averageProgress"
        );

    if (totalElement) {
        totalElement.textContent = total;
    }

    if (progressElement) {
        progressElement.textContent =
            inProgress;
    }

    if (completedElement) {
        completedElement.textContent =
            completed;
    }

    if (averageElement) {
        averageElement.textContent =
            `${averageProgress}%`;
    }

}


/* =========================================================
   FILTERS
========================================================= */

function initializeFilters() {

    const filter =
        document.getElementById(
            "statusFilter"
        );

    if (filter) {

        filter.addEventListener(
            "change",
            function () {

                renderCourses();

            }
        );

    }

    const refreshButton =
        document.getElementById(
            "refreshBtn"
        );

    if (refreshButton) {

        refreshButton.addEventListener(
            "click",
            async function () {

                const button = this;

                button.disabled = true;

                button.textContent =
                    "↻ Loading...";

                await loadCourses();

                button.disabled = false;

                button.textContent =
                    "↻ Refresh";

            }
        );

    }

    const coursesContainer =
        document.getElementById(
            "coursesContainer"
        );

    if (coursesContainer) {

        coursesContainer.addEventListener(
            "click",
            function (event) {

                if (!(event.target instanceof Element)) {
                    return;
                }

                const button =
                    event.target.closest(
                        "[data-course-action='remove']"
                    );

                if (!(button instanceof HTMLButtonElement)) {
                    return;
                }

                const courseCode =
                    button.dataset.courseCode;

                if (!courseCode) {
                    showPageMessage(
                        "Course could not be identified.",
                        "error"
                    );
                    return;
                }

                removeStudentCourse(
                    courseCode,
                    button
                );

            }
        );

    }

}


/* =========================================================
   RENDER COURSES
========================================================= */

function renderCourses() {

    const container =
        document.getElementById(
            "coursesContainer"
        );

    const emptyState =
        document.getElementById(
            "emptyState"
        );

    const filterElement =
        document.getElementById(
            "statusFilter"
        );

    if (!container || !emptyState) {
        return;
    }

    const filter =
        filterElement
            ? filterElement.value
            : "all";

    let courses =
        [...allCourses];

    if (filter !== "all") {

        courses =
            courses.filter(
                function (course) {

                    return normalizeStatus(
                        course.status
                    ) === filter;

                }
            );

    }

    const countText =
        document.getElementById(
            "courseCountText"
        );

    if (countText) {

        countText.textContent =
            `${courses.length} course${
                courses.length === 1
                    ? ""
                    : "s"
            } found`;

    }

    if (courses.length === 0) {

        container.innerHTML = "";

        emptyState.style.display =
            "block";

        return;

    }

    emptyState.style.display =
        "none";

    container.innerHTML =
        courses.map(
            function (course) {

                return createCourseCard(
                    course
                );

            }
        ).join("");

}


/* =========================================================
   COURSE CARD
========================================================= */

function createCourseCard(course) {

    /*
       IMPORTANT:

       course_id = CSE005

       This is what we now use
       for update API calls.
    */

    const courseCode =
        course.course_id ||
        course.course_code ||
        course.code ||
        "-";

    const courseName =
        course.course_name ||
        course.name ||
        "Course";

    const branch =
        course.branch ||
        "Engineering";

    const semester =
        course.semester ??
        "-";

    const difficulty =
        course.difficulty ??
        "-";

    const status =
        normalizeStatus(
            course.status
        );

    const progress =
        getProgress(course);

    const score =
        getScore(course);

    const detailUrl =
        courseCode !== "-"
            ? `course-details.html?id=${
                encodeURIComponent(
                    courseCode
                )
            }`
            : "#";

    const statusText =
        getStatusText(status);

    const statusClass =
        getStatusClass(status);

    /*
       Use a safe unique ID for HTML elements.

       Example:
       CSE005 -> CSE005
       CSE008 -> CSE008
    */

    const safeId =
        String(courseCode)
            .replace(
                /[^a-zA-Z0-9_-]/g,
                "_"
            );

    return `
        <article
            class="my-course-card card"
            data-course-id="${escapeHtml(
                courseCode
            )}"
        >

            <div class="my-course-header">

                <span class="course-code">
                    ${escapeHtml(
                        courseCode
                    )}
                </span>

                <span
                    class="badge course-status ${statusClass}"
                >
                    ${escapeHtml(
                        statusText
                    )}
                </span>

            </div>


            <h3 class="my-course-title">
                ${escapeHtml(
                    courseName
                )}
            </h3>


            <p class="my-course-description">
                ${escapeHtml(
                    course.description ||
                    "Continue learning and track your progress in this course."
                )}
            </p>


            <div class="course-meta">

                <span class="course-meta-item">
                    ${escapeHtml(
                        branch
                    )}
                </span>

                <span class="course-meta-item">
                    Semester
                    ${escapeHtml(
                        semester
                    )}
                </span>

                <span class="course-meta-item">
                    Difficulty
                    ${escapeHtml(
                        difficulty
                    )}
                </span>

            </div>


            <div class="progress-section">

                <div class="progress-header">

                    <span>
                        Course Progress
                    </span>

                    <strong>
                        ${progress}%
                    </strong>

                </div>

                <div class="progress-track">

                    <div
                        class="progress-fill"
                        style="width: ${progress}%"
                    ></div>

                </div>

            </div>


            <div class="score-row">

                <span class="score-label">
                    Score
                </span>

                <span class="score-value">
                    ${formatScore(score)}
                </span>

            </div>


            <div class="course-actions">

                <a
                    href="${detailUrl}"
                    class="btn btn-secondary"
                >
                    View Details
                </a>

                <button
                    type="button"
                    class="btn btn-primary"
                    onclick="toggleUpdatePanel('${safeId}')"
                >
                    Update Progress
                </button>

                <button
                    type="button"
                    class="btn btn-danger"
                    data-course-action="remove"
                    data-course-code="${escapeHtml(courseCode)}"
                    aria-label="Remove ${escapeHtml(courseName)} from My Courses"
                >
                    Remove
                </button>

            </div>


            <div
                id="update-panel-${safeId}"
                class="update-panel"
            >

                <div class="update-panel-title">
                    Update Course
                </div>


                <div class="update-fields">

                    <!-- STATUS -->

                    <div class="update-field">

                        <label>
                            Status
                        </label>

                        <select
                            id="status-${safeId}"
                        >

                            <option
                                value="not_started"
                                ${
                                    status ===
                                    "not_started"
                                        ? "selected"
                                        : ""
                                }
                            >
                                Not Started
                            </option>

                            <option
                                value="in_progress"
                                ${
                                    status ===
                                    "in_progress"
                                        ? "selected"
                                        : ""
                                }
                            >
                                In Progress
                            </option>

                            <option
                                value="completed"
                                ${
                                    status ===
                                    "completed"
                                        ? "selected"
                                        : ""
                                }
                            >
                                Completed
                            </option>

                        </select>

                    </div>


                    <!-- PROGRESS -->

                    <div class="update-field">

                        <label>
                            Progress %
                        </label>

                        <input
                            id="progress-${safeId}"
                            type="number"
                            min="0"
                            max="100"
                            value="${progress}"
                        >

                    </div>


                    <!-- SCORE -->

                    <div class="update-field">

                        <label>
                            Score
                        </label>

                        <input
                            id="score-${safeId}"
                            type="number"
                            min="0"
                            max="100"
                            value="${
                                score !== null
                                    ? score
                                    : ""
                            }"
                            placeholder="Optional"
                        >

                    </div>


                    <!-- TIME -->

                    <div class="update-field">

                        <label>
                            Time Spent (minutes)
                        </label>

                        <input
                            id="time-${safeId}"
                            type="number"
                            min="0"
                            value="${
                                getTimeSpent(course)
                            }"
                        >

                    </div>

                </div>


                <div class="update-actions">

                    <button
                        type="button"
                        class="btn btn-primary"
                        onclick="saveCourseUpdate('${safeId}', '${escapeHtml(courseCode)}')"
                    >
                        Save Changes
                    </button>

                    <button
                        type="button"
                        class="btn btn-secondary"
                        onclick="toggleUpdatePanel('${safeId}')"
                    >
                        Cancel
                    </button>

                </div>

            </div>

        </article>
    `;

}


/* =========================================================
   REMOVE COURSE FROM MY COURSES
========================================================= */

async function removeStudentCourse(
    courseCode,
    button
) {

    const course =
        allCourses.find(
            function (item) {
                return item.course_id === courseCode;
            }
        );

    const courseName =
        course?.course_name ||
        courseCode;

    if (!window.confirm(
        `Remove "${courseName}" from My Courses? Its saved progress will also be removed.`
    )) {
        return;
    }

    button.disabled = true;
    button.textContent = "Removing...";

    try {

        const response =
            await apiDelete(
                `/student/${studentId}/courses/${encodeURIComponent(courseCode)}`
            );

        if (!response || !response.success) {
            throw new Error(
                response?.message ||
                "Unable to remove this course."
            );
        }

        allCourses =
            allCourses.filter(
                function (item) {
                    return item.course_id !== courseCode;
                }
            );

        updateSummary();
        renderCourses();

        showPageMessage(
            response.message ||
            "Course removed from My Courses.",
            "success"
        );

    } catch (error) {

        console.error(
            "Course removal error:",
            error
        );

        button.disabled = false;
        button.textContent = "Remove";

        showPageMessage(
            error.message ||
            "Unable to remove this course.",
            "error"
        );

    }

}


/* =========================================================
   TOGGLE UPDATE PANEL
========================================================= */

function toggleUpdatePanel(courseId) {

    const panel =
        document.getElementById(
            `update-panel-${courseId}`
        );

    if (!panel) {

        console.error(
            "Update panel not found:",
            courseId
        );

        return;
    }

    panel.classList.toggle("open");

}


/* =========================================================
   SAVE COURSE UPDATE
========================================================= */

async function saveCourseUpdate(
    safeId,
    courseCode
) {

    console.log(
        "================================="
    );

    console.log(
        "SAVE BUTTON CLICKED"
    );

    console.log(
        "Course Code:",
        courseCode
    );

    console.log(
        "Student ID:",
        studentId
    );

    console.log(
        "================================="
    );


    const statusElement =
        document.getElementById(
            `status-${safeId}`
        );

    const progressElement =
        document.getElementById(
            `progress-${safeId}`
        );

    const scoreElement =
        document.getElementById(
            `score-${safeId}`
        );

    const timeElement =
        document.getElementById(
            `time-${safeId}`
        );


    if (
        !statusElement ||
        !progressElement ||
        !scoreElement ||
        !timeElement
    ) {

        console.error(
            "Update fields not found."
        );

        showPageMessage(
            "Update form could not be found.",
            "error"
        );

        return;
    }


    const status =
        statusElement.value;

    const progress =
        Number(
            progressElement.value
        );

    const scoreText =
        scoreElement.value.trim();

    const timeSpent =
        Number(
            timeElement.value
        );


    console.log(
        "Status:",
        status
    );

    console.log(
        "Progress:",
        progress
    );

    console.log(
        "Score:",
        scoreText
    );

    console.log(
        "Time:",
        timeSpent
    );


    /* =====================================================
       VALIDATION
    ===================================================== */

    if (
        Number.isNaN(progress) ||
        progress < 0 ||
        progress > 100
    ) {

        showPageMessage(
            "Progress must be between 0 and 100.",
            "error"
        );

        return;
    }


    if (
        scoreText !== "" &&
        (
            Number.isNaN(
                Number(scoreText)
            ) ||
            Number(scoreText) < 0 ||
            Number(scoreText) > 100
        )
    ) {

        showPageMessage(
            "Score must be between 0 and 100.",
            "error"
        );

        return;
    }


    if (
        Number.isNaN(timeSpent) ||
        timeSpent < 0
    ) {

        showPageMessage(
            "Time spent cannot be negative.",
            "error"
        );

        return;
    }


    try {

        /* =================================================
           STEP 1
           UPDATE STUDENT COURSE
        ================================================= */

        const courseData = {

            status: status,

            score:
                scoreText === ""
                    ? null
                    : Number(scoreText)

        };


        console.log(
            "Course API URL:",
            `/student/${studentId}/courses/${courseCode}`
        );

        console.log(
            "Course API data:",
            courseData
        );


        const courseResponse =
            await apiPut(
                `/student/${studentId}/courses/${encodeURIComponent(courseCode)}`,
                courseData
            );


        console.log(
            "Course update response:",
            courseResponse
        );


        if (
            !courseResponse ||
            !courseResponse.success
        ) {

            throw new Error(
                courseResponse?.message ||
                "Failed to update course."
            );

        }


        /* =================================================
           STEP 2
           UPDATE PROGRESS
        ================================================= */

        const progressData = {

            progress_percent:
                progress,

            time_spent_minutes:
                timeSpent

        };


        console.log(
            "Progress API URL:",
            `/student/${studentId}/progress/${courseCode}`
        );

        console.log(
            "Progress API data:",
            progressData
        );


        const progressResponse =
            await apiPut(
                `/student/${studentId}/progress/${encodeURIComponent(courseCode)}`,
                progressData
            );


        console.log(
            "Progress update response:",
            progressResponse
        );


        if (
            !progressResponse ||
            !progressResponse.success
        ) {

            throw new Error(
                progressResponse?.message ||
                "Failed to update progress."
            );

        }


        /* =================================================
           SUCCESS
        ================================================= */

        showPageMessage(
            "Course updated successfully.",
            "success"
        );


        /* CLOSE PANEL */

        const panel =
            document.getElementById(
                `update-panel-${safeId}`
            );

        if (panel) {

            panel.classList.remove(
                "open"
            );

        }


        /* RELOAD DATA */

        await loadCourses();


    } catch (error) {

        console.error(
            "SAVE COURSE ERROR:",
            error
        );

        showPageMessage(
            error.message ||
            "Unable to update course.",
            "error"
        );

    }

}


/* =========================================================
   NORMALIZE STATUS
========================================================= */

function normalizeStatus(status) {

    if (!status) {
        return "not_started";
    }

    const value =
        String(status)
            .toLowerCase()
            .trim();


    if (
        value === "completed" ||
        value === "complete"
    ) {

        return "completed";

    }


    if (
        value === "in_progress" ||
        value === "in-progress" ||
        value === "progress"
    ) {

        return "in_progress";

    }


    return "not_started";

}


/* =========================================================
   STATUS TEXT
========================================================= */

function getStatusText(status) {

    if (
        status === "completed"
    ) {

        return "Completed";

    }

    if (
        status === "in_progress"
    ) {

        return "In Progress";

    }

    return "Not Started";

}


/* =========================================================
   STATUS CLASS
========================================================= */

function getStatusClass(status) {

    if (
        status === "completed"
    ) {

        return "status-completed";

    }

    if (
        status === "in_progress"
    ) {

        return "status-in-progress";

    }

    return "status-not-started";

}


/* =========================================================
   GET PROGRESS
========================================================= */

function getProgress(course) {

    const value =
        course.progress_percent ??
        course.progress ??
        course.progress_percentage ??
        0;


    const number =
        Number(value);


    if (
        Number.isNaN(number)
    ) {

        return 0;

    }


    return Math.max(
        0,
        Math.min(
            100,
            Math.round(number)
        )
    );

}


/* =========================================================
   GET SCORE
========================================================= */

function getScore(course) {

    const value =
        course.score ??
        course.course_score ??
        null;


    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return null;

    }


    const number =
        Number(value);


    if (
        Number.isNaN(number)
    ) {

        return null;

    }


    return number;

}


/* =========================================================
   FORMAT SCORE
========================================================= */

function formatScore(score) {

    if (
        score === null ||
        score === undefined
    ) {

        return "Not available";

    }

    return `${formatNumber(
        score,
        1
    )} / 100`;

}


/* =========================================================
   TIME SPENT
========================================================= */

function getTimeSpent(course) {

    const value =
        course.time_spent_minutes ??
        course.time_spent ??
        0;


    const number =
        Number(value);


    if (
        Number.isNaN(number)
    ) {

        return 0;

    }


    return Math.max(
        0,
        Math.round(number)
    );

}


/* =========================================================
   LOADING
========================================================= */

function showLoading(show) {

    const loading =
        document.getElementById(
            "coursesLoading"
        );

    if (!loading) {
        return;
    }

    if (show) {

        loading.style.display =
            "block";

    } else {

        loading.style.display =
            "none";

    }

}


/* =========================================================
   PAGE MESSAGE
========================================================= */

function showPageMessage(
    message,
    type
) {

    const element =
        document.getElementById(
            "pageMessage"
        );

    if (!element) {
        return;
    }

    element.textContent =
        message;

    element.className =
        `message ${type}`;

    setTimeout(
        function () {

            element.className =
                "message";

            element.textContent =
                "";

        },
        4000
    );

}