const studentId = getStudentId();

if (studentId) {
    initializeLearningPath();
}


/* =========================================================
   INITIALIZE
========================================================= */

async function initializeLearningPath() {
    const generateButton =
        document.getElementById("generatePathBtn");

    const emptyGenerateButton =
        document.getElementById("emptyGenerateBtn");

    if (generateButton) {
        generateButton.addEventListener(
            "click",
            generateLearningPath
        );
    }

    if (emptyGenerateButton) {
        emptyGenerateButton.addEventListener(
            "click",
            generateLearningPath
        );
    }

    await loadLearningPath();
}


/* =========================================================
   LOAD LEARNING PATH
========================================================= */

async function loadLearningPath() {

    showLoading();

    hideError();

    try {

        const response = await apiGet(
            `/student/${studentId}/learning-path`
        );

        console.log(
            "FULL LEARNING PATH RESPONSE:",
            response
        );

        if (!response || response.success === false) {

            throw new Error(
                response?.message ||
                "Failed to load learning path."
            );
        }


        /*
         * Extract learning path from different
         * possible backend response structures.
         */

        let path = null;
        let courses = [];


        if (response.learning_path) {

            path = response.learning_path;

            courses =
                response.courses ||
                response.learning_path.courses ||
                [];
        }


        else if (response.path) {

            path = response.path;

            courses =
                response.courses ||
                response.path.courses ||
                [];
        }


        else if (response.data) {

            if (response.data.learning_path) {

                path =
                    response.data.learning_path;

                courses =
                    response.data.courses ||
                    response.data.learning_path.courses ||
                    [];
            }


            else if (response.data.path) {

                path =
                    response.data.path;

                courses =
                    response.data.courses ||
                    response.data.path.courses ||
                    [];
            }


            else if (
                typeof response.data === "object"
            ) {

                path = response.data;

                courses =
                    response.data.courses ||
                    [];
            }
        }


        /*
         * Direct response object.
         */

        if (!path) {

            if (
                response.id ||
                response.learning_path_id ||
                response.path_name
            ) {

                path = response;

                courses =
                    response.courses ||
                    [];
            }
        }


        console.log(
            "Detected learning path:",
            path
        );

        console.log(
            "Detected courses:",
            courses
        );


        hideLoading();


        /*
         * No path exists.
         */

        if (!path) {

            showEmptyState();

            return;
        }


        /*
         * Make sure courses is an array.
         */

        if (!Array.isArray(courses)) {
            courses = [];
        }


        renderLearningPath(
            path,
            courses
        );


    } catch (error) {

        console.error(
            "Learning path loading error:",
            error
        );

        hideLoading();

        showError(
            error.message ||
            "Unable to load learning path."
        );
    }
}


/* =========================================================
   GENERATE LEARNING PATH
========================================================= */

async function generateLearningPath() {

    const button =
        document.getElementById(
            "generatePathBtn"
        );

    const emptyButton =
        document.getElementById(
            "emptyGenerateBtn"
        );


    if (button) {

        button.disabled = true;

        button.textContent =
            "Generating...";
    }


    if (emptyButton) {

        emptyButton.disabled = true;
    }


    showLoading();

    hideError();


    try {

        const response = await apiPost(
            `/student/${studentId}/learning-path/generate`,
            {}
        );


        console.log(
            "Learning path generation response:",
            response
        );


        if (
            !response ||
            response.success === false
        ) {

            throw new Error(
                response?.message ||
                "Failed to generate learning path."
            );
        }


        /*
         * The POST endpoint may return only:
         *
         * success: true
         * message: "Learning path generated"
         *
         * Therefore we always reload the GET endpoint.
         */

        console.log(
            "Generation succeeded. Fetching learning path..."
        );


        await loadLearningPath();


    } catch (error) {

        console.error(
            "Learning path generation error:",
            error
        );

        hideLoading();

        showError(
            error.message ||
            "Unable to generate learning path."
        );


    } finally {

        if (button) {

            button.disabled = false;

            button.innerHTML =
                "✦ Generate Learning Path";
        }


        if (emptyButton) {

            emptyButton.disabled = false;
        }
    }
}


/* =========================================================
   RENDER LEARNING PATH
========================================================= */

function renderLearningPath(
    path,
    courses
) {

    const pathSummary =
        document.getElementById(
            "pathSummary"
        );

    const pathSection =
        document.getElementById(
            "pathSection"
        );

    const emptyState =
        document.getElementById(
            "emptyState"
        );

    const timeline =
        document.getElementById(
            "timeline"
        );


    if (!timeline) {

        console.error(
            "Element #timeline not found in HTML."
        );

        return;
    }


    /*
     * Hide empty state.
     */

    if (emptyState) {

        emptyState.style.display =
            "none";
    }


    /*
     * Show summary.
     */

    if (pathSummary) {

        pathSummary.style.display =
            "grid";
    }


    /*
     * Show path section.
     */

    if (pathSection) {

        pathSection.style.display =
            "block";
    }


    /*
     * Path information.
     */

    const pathName =
        path.path_name ||
        path.name ||
        "Personalized Learning Path";


    const description =
        path.description ||
        "Your recommended course sequence based on your learning profile.";


    const totalCourses =
        path.total_courses ??
        courses.length ??
        0;


    const estimatedHours =
        path.estimated_hours ??
        0;


    const status =
        path.status ||
        "active";


    /*
     * Update summary.
     */

    setText(
        "totalCourses",
        totalCourses
    );


    setText(
        "estimatedHours",
        estimatedHours
    );


    setText(
        "pathStatus",
        formatText(status)
    );


    /*
     * Update title and description.
     */

    setText(
        "pathName",
        pathName
    );


    setText(
        "pathDescription",
        description
    );


    /*
     * No courses returned.
     */

    if (
        !Array.isArray(courses) ||
        courses.length === 0
    ) {

        timeline.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📚</div>

                <h3>
                    No courses in this learning path
                </h3>

                <p>
                    The learning path was created,
                    but no courses were returned.
                </p>
            </div>
        `;

        return;
    }


    /*
     * Sort courses by sequence.
     */

    courses.sort(function (a, b) {

        const sequenceA =
            Number(
                a.sequence ??
                a.sequence_number ??
                999
            );

        const sequenceB =
            Number(
                b.sequence ??
                b.sequence_number ??
                999
            );

        return sequenceA - sequenceB;
    });


    /*
     * Render timeline.
     */

    timeline.innerHTML =
        courses.map(
            function (course, index) {

                const sequence =
                    course.sequence ??
                    course.sequence_number ??
                    index + 1;


                const courseName =
                    course.course_name ||
                    course.name ||
                    "Course";


                const courseId =
                    course.course_id ||
                    course.code ||
                    "";


                const branch =
                    course.branch ||
                    "";


                const category =
                    course.category ||
                    "";


                const difficulty =
                    course.difficulty ??
                    "";


                const level =
                    course.course_level ||
                    "";


                const credits =
                    course.credits ??
                    "";


                const courseStatus =
                    course.status ||
                    "locked";


                return `
                    <div class="learning-path-item">

                        <div class="learning-path-number">
                            ${escapeHtml(sequence)}
                        </div>

                        <div class="learning-path-content">

                            <div class="learning-path-course-header">

                                <div>

                                    <span class="course-code">
                                        ${escapeHtml(courseId)}
                                    </span>

                                    <h3>
                                        ${escapeHtml(courseName)}
                                    </h3>

                                </div>

                                <span class="badge">
                                    ${escapeHtml(
                                        formatText(
                                            courseStatus
                                        )
                                    )}
                                </span>

                            </div>


                            <div class="learning-path-meta">

                                ${
                                    branch
                                        ? `
                                        <span>
                                            ${escapeHtml(branch)}
                                        </span>
                                        `
                                        : ""
                                }


                                ${
                                    category
                                        ? `
                                        <span>
                                            ${escapeHtml(category)}
                                        </span>
                                        `
                                        : ""
                                }


                                ${
                                    level
                                        ? `
                                        <span>
                                            ${escapeHtml(level)}
                                        </span>
                                        `
                                        : ""
                                }


                                ${
                                    credits !== ""
                                        ? `
                                        <span>
                                            ${escapeHtml(
                                                credits
                                            )} Credits
                                        </span>
                                        `
                                        : ""
                                }


                                ${
                                    difficulty !== ""
                                        ? `
                                        <span>
                                            Difficulty:
                                            ${escapeHtml(
                                                difficulty
                                            )}
                                        </span>
                                        `
                                        : ""
                                }

                            </div>


                            <div class="learning-path-course-actions">

                                ${
                                    courseId
                                        ? `
                                        <a
                                            href="course-details.html?id=${encodeURIComponent(courseId)}"
                                            class="btn btn-secondary"
                                        >
                                            View Course
                                        </a>
                                        `
                                        : ""
                                }

                            </div>

                        </div>

                    </div>
                `;
            }
        ).join("");
}


/* =========================================================
   EMPTY STATE
========================================================= */

function showEmptyState() {

    const pathSummary =
        document.getElementById(
            "pathSummary"
        );

    const pathSection =
        document.getElementById(
            "pathSection"
        );

    const emptyState =
        document.getElementById(
            "emptyState"
        );


    if (pathSummary) {

        pathSummary.style.display =
            "none";
    }


    if (pathSection) {

        pathSection.style.display =
            "none";
    }


    if (emptyState) {

        emptyState.style.display =
            "block";
    }
}


/* =========================================================
   LOADING
========================================================= */

function showLoading() {

    const loading =
        document.getElementById(
            "loading"
        );

    if (loading) {

        loading.style.display =
            "flex";
    }
}


function hideLoading() {

    const loading =
        document.getElementById(
            "loading"
        );

    if (loading) {

        loading.style.display =
            "none";
    }
}


/* =========================================================
   ERROR
========================================================= */

function showError(message) {

    const errorElement =
        document.getElementById(
            "errorMessage"
        );


    if (!errorElement) {
        return;
    }


    errorElement.textContent =
        message || "Something went wrong.";


    errorElement.style.display =
        "block";
}


function hideError() {

    const errorElement =
        document.getElementById(
            "errorMessage"
        );


    if (errorElement) {

        errorElement.textContent =
            "";

        errorElement.style.display =
            "none";
    }
}


/* =========================================================
   HELPERS
========================================================= */

function setText(
    elementId,
    value
) {

    const element =
        document.getElementById(
            elementId
        );


    if (element) {

        element.textContent =
            value ?? "-";
    }
}


function formatText(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return "-";
    }


    return String(value)
        .replaceAll("_", " ")
        .replace(
            /\b\w/g,
            function (letter) {
                return letter.toUpperCase();
            }
        );
}


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