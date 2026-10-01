let studentId = null;
let originalProfile = null;


/* =========================================================
   INITIALIZATION
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    studentId = getStudentId();

    if (!studentId) {
        return;
    }

    setupForm();

    loadProfile();

});


/* =========================================================
   FORM SETUP
   ========================================================= */

function setupForm() {

    const form =
        document.getElementById("profileForm");

    const resetButton =
        document.getElementById("resetProfileBtn");


    if (form) {

        form.addEventListener(
            "submit",
            saveProfile
        );

    }


    if (resetButton) {

        resetButton.addEventListener(
            "click",
            resetProfile
        );

    }

}


/* =========================================================
   LOAD PROFILE
   ========================================================= */

async function loadProfile() {

    showLoading();

    hideMessages();


    try {

        const response =
            await apiGet(
                `/profile/${studentId}`
            );


        if (!response.success) {

            throw new Error(
                response.message ||
                "Unable to load profile."
            );

        }


        /*
         * Backend currently returns profile information.
         */

        const profile =
            response.profile ||
            response.data ||
            {};


        const user =
            response.user ||
            profile.user ||
            {};


        originalProfile = {

            student_name:
                profile.student_name ||
                "",

            username:
                user.username ||
                profile.username ||
                "",

            email:
                user.email ||
                profile.email ||
                "",

            branch:
                profile.branch ||
                "",

            semester:
                profile.semester ||
                "",

            interests:
                profile.interests ||
                "",

            preferred_difficulty:
                profile.preferred_difficulty ||
                ""

        };


        renderProfile(
            profile,
            user
        );


        fillForm(
            originalProfile
        );


        hideLoading();

        document.getElementById(
            "profileContent"
        ).style.display = "grid";


    } catch (error) {

        console.error(
            "Profile loading error:",
            error
        );


        hideLoading();


        showError(
            error.message ||
            "Unable to load profile."
        );

    }

}


/* =========================================================
   RENDER PROFILE CARD
   ========================================================= */

function renderProfile(profile, user) {

    const name =
        profile.student_name ||
        user.username ||
        "Student";


    const email =
        user.email ||
        profile.email ||
        "-";


    const learningLevel =
        profile.learning_level ||
        "-";


    const academicStrength =
        profile.academic_strength ??
        "-";


    const engagementStrength =
        profile.engagement_strength ??
        "-";


    const readiness =
        profile.readiness_score ??
        "-";


    document.getElementById(
        "profileName"
    ).textContent = name;


    document.getElementById(
        "profileEmail"
    ).textContent = email;


    document.getElementById(
        "profileAvatar"
    ).textContent = getInitials(name);


    document.getElementById(
        "profileLearningLevel"
    ).textContent =
        formatText(learningLevel);


    document.getElementById(
        "profileAcademicStrength"
    ).textContent =
        formatProfileScore(academicStrength);


    document.getElementById(
        "profileEngagementStrength"
    ).textContent =
        formatProfileScore(engagementStrength);


    document.getElementById(
        "profileReadiness"
    ).textContent =
        formatProfileScore(readiness);


    /* Topbar */

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

}


/* =========================================================
   FILL FORM
   ========================================================= */

function fillForm(profile) {

    document.getElementById(
        "studentName"
    ).value =
        profile.student_name || "";


    document.getElementById(
        "username"
    ).value =
        profile.username || "";


    document.getElementById(
        "email"
    ).value =
        profile.email || "";


    document.getElementById(
        "branch"
    ).value =
        profile.branch || "";


    document.getElementById(
        "semester"
    ).value =
        profile.semester || "";


    document.getElementById(
        "interests"
    ).value =
        profile.interests || "";


    document.getElementById(
        "preferredDifficulty"
    ).value =
        profile.preferred_difficulty || "";

}


/* =========================================================
   SAVE PROFILE
   ========================================================= */

async function saveProfile(event) {

    event.preventDefault();


    hideMessages();


    const saveButton =
        document.getElementById(
            "saveProfileBtn"
        );


    const studentName =
        document.getElementById(
            "studentName"
        ).value.trim();


    const branch =
        document.getElementById(
            "branch"
        ).value;


    const semester =
        document.getElementById(
            "semester"
        ).value;


    const interests =
        document.getElementById(
            "interests"
        ).value.trim();


    const preferredDifficulty =
        document.getElementById(
            "preferredDifficulty"
        ).value;


    /* Validation */

    if (!studentName) {

        showError(
            "Please enter your student name."
        );

        return;
    }


    if (!branch) {

        showError(
            "Please select your engineering branch."
        );

        return;
    }


    if (!semester) {

        showError(
            "Please select your current semester."
        );

        return;
    }


    if (!preferredDifficulty) {

        showError(
            "Please select your preferred course difficulty."
        );

        return;
    }


    /* Loading state */

    saveButton.disabled = true;

    saveButton.dataset.originalText =
        saveButton.textContent;

    saveButton.textContent =
        "Saving...";


    try {

        const response =
            await apiPut(
                `/profile/${studentId}`,
                {
                    student_name:
                        studentName,

                    branch:
                        branch,

                    semester:
                        Number(semester),

                    interests:
                        interests,

                    preferred_difficulty:
                        Number(preferredDifficulty)
                }
            );


        if (!response.success) {

            throw new Error(
                response.message ||
                "Unable to update profile."
            );

        }


        showSuccess(
            "Profile updated successfully."
        );


        /*
         * Reload profile so the left card
         * and topbar show fresh information.
         */

        await loadProfile();


    } catch (error) {

        console.error(
            "Profile update error:",
            error
        );


        showError(
            error.message ||
            "Unable to update profile."
        );

    } finally {

        saveButton.disabled = false;

        saveButton.textContent =
            saveButton.dataset.originalText ||
            "Save Changes";

    }

}


/* =========================================================
   RESET
   ========================================================= */

function resetProfile() {

    if (!originalProfile) {
        return;
    }


    fillForm(
        originalProfile
    );


    hideMessages();

}


/* =========================================================
   FORMAT SCORE
   ========================================================= */

function formatProfileScore(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "-";
    }


    const number =
        Number(value);


    if (Number.isNaN(number)) {

        return formatText(value);

    }


    /*
     * Readiness/strength values can be
     * represented either as 0-1 or 0-100.
     */

    if (
        number >= 0 &&
        number <= 1
    ) {

        return `${Math.round(number * 100)}%`;

    }


    return `${Math.round(number)}%`;

}


/* =========================================================
   UI HELPERS
   ========================================================= */

function showLoading() {

    document.getElementById(
        "loading"
    ).style.display = "flex";


    document.getElementById(
        "profileContent"
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

    element.style.display =
        "block";

}


function showSuccess(message) {

    const element =
        document.getElementById(
            "successMessage"
        );


    element.textContent = message;

    element.style.display =
        "block";

}


function hideMessages() {

    document.getElementById(
        "errorMessage"
    ).style.display = "none";


    document.getElementById(
        "successMessage"
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