/* =========================================================
   LEARNAI - COURSE DETAILS JAVASCRIPT
========================================================= */


/* =========================================================
   GLOBAL
========================================================= */

let currentCourse = null;


/* =========================================================
   GET COURSE ID
========================================================= */

function getCourseIdFromURL() {

    const params =
        new URLSearchParams(
            window.location.search
        );


    return params.get("id");

}


/* =========================================================
   LOAD USER
========================================================= */

async function loadUser() {

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


        const nameElement =
            document.getElementById(
                "topbarUserName"
            );


        const avatarElement =
            document.getElementById(
                "topbarAvatar"
            );


        if (nameElement) {
            nameElement.textContent = name;
        }


        if (avatarElement) {
            avatarElement.textContent =
                getInitials(name);
        }


    } catch (error) {

        console.error(
            "User loading error:",
            error
        );

    }

}


/* =========================================================
   LOAD COURSE
========================================================= */

async function loadCourse() {

    const courseId =
        getCourseIdFromURL();


    const loading =
        document.getElementById(
            "courseLoading"
        );


    const content =
        document.getElementById(
            "courseContent"
        );


    const errorContainer =
        document.getElementById(
            "courseError"
        );


    if (!courseId) {

        loading.style.display =
            "none";

        errorContainer.style.display =
            "block";

        return;

    }


    try {

        const data =
            await apiGet(
                `/courses/${encodeURIComponent(courseId)}`
            );


        if (!data.success) {

            throw new Error(
                data.message ||
                "Course not found."
            );

        }


        currentCourse =
            data.course;


        renderCourse(
            currentCourse
        );


        loading.style.display =
            "none";


        content.style.display =
            "block";


    } catch (error) {

        console.error(
            "Course details error:",
            error
        );


        loading.style.display =
            "none";


        errorContainer.style.display =
            "block";

    }

}


/* =========================================================
   RENDER COURSE
========================================================= */

function renderCourse(course) {

    const courseId =
        course.course_id ||
        "-";


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


    /* =====================================================
       HERO
    ====================================================== */

    document.querySelector(
        ".course-code"
    ).textContent =
        courseId;


    document.getElementById(
        "courseName"
    ).textContent =
        courseName;


    document.getElementById(
        "courseCategory"
    ).textContent =
        category;


    document.getElementById(
        "courseBranch"
    ).textContent =
        branch;


    document.getElementById(
        "courseLevel"
    ).textContent =
        level;


    document.getElementById(
        "courseDifficulty"
    ).textContent =
        difficulty;


    const coreElement =
        document.getElementById(
            "courseCore"
        );


    if (isCore) {

        coreElement.textContent =
            "Core Course";

        coreElement.className =
            "badge badge-success";

        coreElement.style.display =
            "inline-flex";

    } else {

        coreElement.style.display =
            "none";

    }


    /* =====================================================
       DESCRIPTION
    ====================================================== */

    document.getElementById(
        "courseDescription"
    ).textContent =
        course.description ||
        `Study ${courseName} and develop relevant engineering skills through this course.`;


    /* =====================================================
       INFORMATION
    ====================================================== */

    document.getElementById(
        "infoCourseId"
    ).textContent =
        courseId;


    document.getElementById(
        "infoBranch"
    ).textContent =
        branch;


    document.getElementById(
        "infoSemester"
    ).textContent =
        semester;


    document.getElementById(
        "infoCredits"
    ).textContent =
        credits;


    document.getElementById(
        "infoDifficulty"
    ).textContent =
        `${difficulty} / 5`;


    document.getElementById(
        "infoLevel"
    ).textContent =
        level;


    document.getElementById(
        "infoCategory"
    ).textContent =
        category;


    /* =====================================================
       SKILLS
    ====================================================== */

    renderSkills(
        course.skills
    );


    /* =====================================================
       PREREQUISITES
    ====================================================== */

    renderPrerequisites(
        course.prerequisites
    );

}


/* =========================================================
   SKILLS
========================================================= */

function renderSkills(value) {

    const container =
        document.getElementById(
            "skillsContainer"
        );


    const skills =
        parseList(value);


    if (skills.length === 0) {

        container.innerHTML = `
            <span class="no-data">
                No specific skills listed.
            </span>
        `;

        return;

    }


    container.innerHTML =
        skills
            .map(
                function(skill) {

                    return `
                        <span class="detail-tag">
                            ${escapeHtml(skill)}
                        </span>
                    `;

                }
            )
            .join("");

}


/* =========================================================
   PREREQUISITES
========================================================= */

function renderPrerequisites(value) {

    const container =
        document.getElementById(
            "prerequisitesContainer"
        );


    const prerequisites =
        parseList(value);


    if (prerequisites.length === 0) {

        container.innerHTML = `
            <span class="no-data">
                No specific prerequisites.
            </span>
        `;

        return;

    }


    container.innerHTML =
        prerequisites
            .map(
                function(item) {

                    return `
                        <div class="prerequisite-item">
                            ${escapeHtml(item)}
                        </div>
                    `;

                }
            )
            .join("");

}


/* =========================================================
   ADD COURSE
========================================================= */

async function addCourseToMyCourses() {

    const studentId =
        getStudentId();


    if (!studentId) {
        return;
    }


    if (!currentCourse) {
        return;
    }


    const button =
        document.getElementById(
            "addCourseBtn"
        );


    const message =
        document.getElementById(
            "courseMessage"
        );


    button.disabled =
        true;


    button.textContent =
        "Adding...";


    try {

        const courseId =
            currentCourse.course_id;

        if (!courseId) {
            throw new Error("This course does not have a valid course ID.");
        }


        const data =
            await apiPost(
                `/student/${studentId}/courses`,
                {
                    course_id: courseId,
                    status: "not_started"
                }
            );


        if (!data.success) {

            throw new Error(
                data.message ||
                "Unable to add course."
            );

        }


        message.className =
            "message success";


        message.textContent =
            "Course added to My Courses successfully.";


        button.textContent =
            "✓ Added to My Courses";


        button.classList.remove(
            "btn-primary"
        );


        button.classList.add(
            "btn-secondary"
        );


    } catch (error) {

        console.error(
            "Add course error:",
            error
        );


        message.className =
            "message error";


        message.textContent =
            error.message ||
            "Unable to add course.";


        button.disabled =
            false;


        button.textContent =
            "+ Add to My Courses";

    }

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


        await loadUser();

        await loadCourse();


        const addButton =
            document.getElementById(
                "addCourseBtn"
            );


        if (addButton) {

            addButton.addEventListener(
                "click",
                addCourseToMyCourses
            );

        }

    }
);