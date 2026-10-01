/* =========================================================
   LEARNAI - COURSES JAVASCRIPT
========================================================= */


let courses = [];


/* =========================================================
   LOAD COURSES
========================================================= */

async function loadCourses() {

    const container =
        document.getElementById("coursesContainer");

    container.innerHTML = `
        <div class="loading">
            Loading courses...
        </div>
    `;


    try {

        const search =
            document.getElementById("courseSearch").value.trim();

        const branch =
            document.getElementById("branchFilter").value;

        const semester =
            document.getElementById("semesterFilter").value;


        const params = new URLSearchParams();


        if (search) {
            params.append("search", search);
        }


        if (branch) {
            params.append("branch", branch);
        }


        if (semester) {
            params.append("semester", semester);
        }


        const query =
            params.toString()
                ? `?${params.toString()}`
                : "";


        const data =
            await apiGet(`/courses${query}`);


        if (!data.success) {

            throw new Error(
                data.message ||
                "Unable to load courses."
            );

        }


        courses =
            Array.isArray(data.courses)
                ? data.courses
                : [];


        document.getElementById(
            "courseCount"
        ).textContent = courses.length;


        renderCourses(courses);


    } catch (error) {

        console.error(
            "Course loading error:",
            error
        );


        document.getElementById(
            "courseCount"
        ).textContent = "0";


        container.innerHTML = `
            <div class="courses-error">

                ${escapeHtml(
                    error.message ||
                    "Unable to load courses."
                )}

            </div>
        `;

    }

}


/* =========================================================
   RENDER COURSES
========================================================= */

function renderCourses(courseList) {

    const container =
        document.getElementById(
            "coursesContainer"
        );


    if (
        !courseList ||
        courseList.length === 0
    ) {

        container.innerHTML = `
            <div class="courses-empty card">

                <div class="courses-empty-icon">
                    ▣
                </div>

                <h3>
                    No courses found
                </h3>

                <p>
                    Try changing your search or filters.
                </p>

            </div>
        `;

        return;
    }


    container.innerHTML =
        courseList
            .map(
                function(course) {

                    return createCourseCard(
                        course
                    );

                }
            )
            .join("");
}


/* =========================================================
   COURSE CARD
========================================================= */

function createCourseCard(course) {

    const courseId =
        course.course_id || "-";


    const courseName =
        course.course_name ||
        "Untitled Course";


    const branch =
        course.branch ||
        "-";


    const semester =
        course.semester ??
        "-";


    const category =
        course.category ||
        "-";


    const difficulty =
        course.difficulty ??
        "-";


    const credits =
        course.credits ??
        "-";


    const level =
        course.course_level ||
        "-";


    const isCore =
        Number(course.is_core) === 1 ||
        course.is_core === true;


    const skills =
        parseList(course.skills);


    const skillHTML =
        skills.length > 0

            ? skills
                .slice(0, 6)
                .map(
                    function(skill) {

                        return `
                            <span class="skill-tag">
                                ${escapeHtml(skill)}
                            </span>
                        `;

                    }
                )
                .join("")

            : `
                <span class="course-description">
                    Skills not specified.
                </span>
            `;


    return `

        <article class="course-card card">

            <div class="course-card-header">

                <div>

                    <div class="course-id">
                        ${escapeHtml(courseId)}
                    </div>

                    <h2>
                        ${escapeHtml(courseName)}
                    </h2>

                </div>


                ${
                    isCore
                        ? `
                            <span class="badge badge-primary core-badge">
                                Core
                            </span>
                          `
                        : ""
                }

            </div>


            <div class="course-info">

                <span>
                    ${escapeHtml(branch)}
                </span>

                <span>
                    Semester ${escapeHtml(semester)}
                </span>

                <span>
                    ${escapeHtml(category)}
                </span>

                <span>
                    ${escapeHtml(credits)} Credits
                </span>

            </div>


            <p class="course-description">

                ${escapeHtml(
                    course.description ||
                    "Explore this engineering course and develop relevant technical skills."
                )}

            </p>


            <div class="course-skills">

                <div class="course-skills-title">
                    Skills
                </div>

                <div class="skill-tags">

                    ${skillHTML}

                </div>

            </div>


            <div class="course-card-footer">

                <div class="course-difficulty">

                    <span>
                        Difficulty
                    </span>

                    <strong>
                        ${escapeHtml(difficulty)} / 5
                    </strong>

                </div>


                <div class="course-difficulty">

                    <span>
                        Level
                    </span>

                    <strong>
                        ${escapeHtml(level)}
                    </strong>

                </div>


                <a
                    href="course-details.html?id=${encodeURIComponent(courseId)}"
                    class="btn btn-secondary">

                    View Details

                </a>

            </div>

        </article>

    `;
}


/* =========================================================
   PARSE LIST
========================================================= */

function parseList(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return [];

    }


    if (Array.isArray(value)) {

        return value
            .filter(Boolean)
            .map(String);

    }


    return String(value)
        .split(/[;,|]/)
        .map(
            function(item) {
                return item.trim();
            }
        )
        .filter(Boolean);

}


/* =========================================================
   FILTER EVENTS
========================================================= */

function initializeCourseFilters() {

    const searchInput =
        document.getElementById(
            "courseSearch"
        );


    const branchFilter =
        document.getElementById(
            "branchFilter"
        );


    const semesterFilter =
        document.getElementById(
            "semesterFilter"
        );


    const clearButton =
        document.getElementById(
            "clearFiltersBtn"
        );


    const refreshButton =
        document.getElementById(
            "refreshCoursesBtn"
        );


    let searchTimer;


    searchInput.addEventListener(
        "input",
        function() {

            clearTimeout(searchTimer);


            searchTimer =
                setTimeout(
                    function() {

                        loadCourses();

                    },
                    350
                );

        }
    );


    branchFilter.addEventListener(
        "change",
        function() {

            loadCourses();

        }
    );


    semesterFilter.addEventListener(
        "change",
        function() {

            loadCourses();

        }
    );


    clearButton.addEventListener(
        "click",
        function() {

            searchInput.value = "";

            branchFilter.value = "";

            semesterFilter.value = "";

            loadCourses();

        }
    );


    refreshButton.addEventListener(
        "click",
        function() {

            loadCourses();

        }
    );

}


/* =========================================================
   TOPBAR
========================================================= */

async function loadCoursePageUser() {

    const studentId =
        getStudentId();


    if (!studentId) {
        return;
    }


    try {

        const data =
            await apiGet(
                `/profile/${studentId}`
            );


        if (!data.success) {
            return;
        }


        const student =
            data.student ||
            data.profile ||
            {};


        const name =
            student.student_name ||
            student.name ||
            "Student";


        document.getElementById(
            "topbarUserName"
        ).textContent = name;


        document.getElementById(
            "topbarAvatar"
        ).textContent =
            getInitials(name);


    } catch (error) {

        console.error(
            "User profile error:",
            error
        );

    }

}


/* =========================================================
   INITIALS
========================================================= */

function getInitials(name) {

    const words =
        String(name || "Student")
            .trim()
            .split(/\s+/);


    if (words.length === 1) {

        return words[0]
            .substring(0, 2)
            .toUpperCase();

    }


    return (
        words[0][0] +
        words[words.length - 1][0]
    ).toUpperCase();

}


/* =========================================================
   INITIALIZE
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    async function() {

        const studentId =
            getStudentId();


        if (!studentId) {
            return;
        }


        initializeCourseFilters();

        await loadCoursePageUser();

        await loadCourses();

    }
);