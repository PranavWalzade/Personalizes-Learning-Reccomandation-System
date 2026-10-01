/* =========================================
   RECOMMENDATIONS PAGE
========================================= */

let studentId = null;
let currentRecommendations = [];


/* =========================================
   INITIALIZATION
========================================= */

document.addEventListener("DOMContentLoaded", function () {

    studentId = getStudentId();

    if (!studentId) {
        return;
    }

    loadUserInfo();
    loadRecommendations();

    const refreshButton = document.getElementById("refreshBtn");

    if (refreshButton) {
        refreshButton.addEventListener("click", function () {
            loadRecommendations();
        });
    }

    const limitSelect = document.getElementById("limitSelect");

    if (limitSelect) {
        limitSelect.addEventListener("change", function () {
            loadRecommendations();
        });
    }

});


/* =========================================
   USER INFO
========================================= */

function loadUserInfo() {

    const user = getCurrentUser();

    if (!user) {
        return;
    }

    const name =
        user.student_name ||
        user.username ||
        user.name ||
        "Student";

    const userName =
        document.getElementById("userName");

    const userAvatar =
        document.getElementById("userAvatar");

    if (userName) {
        userName.textContent = name;
    }

    if (userAvatar) {
        userAvatar.textContent =
            name.charAt(0).toUpperCase();
    }

}


/* =========================================
   LOAD RECOMMENDATIONS
========================================= */

async function loadRecommendations() {

    showLoading();

    try {

        await loadProfile();

        const limitElement =
            document.getElementById("limitSelect");

        const limit =
            limitElement ? limitElement.value : 10;

        const response = await apiGet(
            `/student/${studentId}/recommendations?limit=${limit}`
        );

        if (!response || response.success === false) {

            throw new Error(
                response?.message ||
                "Failed to load recommendations"
            );
        }

        currentRecommendations =
            response.recommendations ||
            response.data?.recommendations ||
            [];

        updateRecommendationCount();

        renderRecommendations();

    }
    catch (error) {

        console.error(
            "Recommendation error:",
            error
        );

        showEmptyState(
            "Unable to load recommendations. Please check that the Flask server is running."
        );

    }

}


/* =========================================
   LOAD PROFILE
========================================= */

async function loadProfile() {

    try {

        const response = await apiGet(
            `/profile/${studentId}`
        );

        if (!response || response.success === false) {
            return;
        }

        const data =
            response.data ||
            response.profile ||
            response;

        const profile =
            data.profile ||
            data.student ||
            data;

        setText(
            "branchValue",
            profile.branch || "-"
        );

        setText(
            "semesterValue",
            profile.semester || "-"
        );

        setText(
            "learningLevelValue",
            formatText(
                profile.learning_level || "-"
            )
        );

        let readiness =
            Number(profile.readiness_score);

        if (!Number.isNaN(readiness)) {

            if (readiness <= 1) {
                readiness = readiness * 100;
            }

            setText(
                "readinessValue",
                `${readiness.toFixed(0)}%`
            );

        }
        else {

            setText(
                "readinessValue",
                "-"
            );

        }

    }
    catch (error) {

        console.error(
            "Profile loading error:",
            error
        );

    }

}


/* =========================================
   RENDER
========================================= */

function renderRecommendations() {

    const grid =
        document.getElementById(
            "recommendationGrid"
        );

    const emptyState =
        document.getElementById(
            "emptyState"
        );

    const loadingState =
        document.getElementById(
            "loadingState"
        );

    if (!grid) {
        return;
    }

    if (loadingState) {
        loadingState.style.display = "none";
    }

    grid.innerHTML = "";

    if (!currentRecommendations.length) {

        if (emptyState) {
            emptyState.style.display = "block";
        }

        return;
    }

    if (emptyState) {
        emptyState.style.display = "none";
    }

    currentRecommendations.forEach(
        function (recommendation, index) {

            grid.insertAdjacentHTML(
                "beforeend",
                createRecommendationCard(
                    recommendation,
                    index
                )
            );

        }
    );

}


/* =========================================
   CREATE CARD
========================================= */

function createRecommendationCard(
    recommendation,
    index
) {

    const course =
        recommendation.course ||
        recommendation;

    const rank =
        recommendation.rank ||
        recommendation.recommendation_rank ||
        index + 1;

    const courseId =
        course.course_id ||
        recommendation.course_id ||
        "";

    const courseName =
        course.course_name ||
        recommendation.course_name ||
        "Course";

    const branch =
        course.branch ||
        recommendation.branch ||
        "-";

    const semester =
        course.semester ||
        recommendation.semester ||
        "-";

    const category =
        course.category ||
        recommendation.category ||
        "-";

    const difficulty =
        course.difficulty ||
        recommendation.difficulty ||
        "-";

    let score =
        recommendation.hybrid_score;

    if (
        score === undefined ||
        score === null
    ) {

        score =
            recommendation.score ||
            recommendation.match_score ||
            0;

    }

    score = Number(score);

    if (score <= 1) {
        score = score * 100;
    }

    score = Math.max(
        0,
        Math.min(100, score)
    );

    const explanation =
        recommendation.explanation ||
        "This course matches your learning profile.";

    return `
        <article class="recommendation-card">

            <div class="recommendation-rank">
                #${escapeHtml(rank)}
            </div>

            <div class="recommendation-header">

                <span class="course-code">
                    ${escapeHtml(courseId)}
                </span>

                <h3 class="course-name">
                    ${escapeHtml(courseName)}
                </h3>

            </div>


            <div class="recommendation-meta">

                <span class="meta-item">
                    ${escapeHtml(branch)}
                </span>

                <span class="meta-item">
                    Semester ${escapeHtml(semester)}
                </span>

                <span class="meta-item">
                    ${escapeHtml(category)}
                </span>

                <span class="meta-item">
                    Difficulty ${escapeHtml(difficulty)}
                </span>

            </div>


            <div class="match-section">

                <div class="match-header">

                    <span class="match-title">
                        AI Match Score
                    </span>

                    <span class="match-score">
                        ${score.toFixed(1)}%
                    </span>

                </div>

                <div class="match-bar">

                    <div
                        class="match-fill"
                        style="width:${score}%"
                    ></div>

                </div>

            </div>


            <div class="explanation-box">

                <span class="explanation-title">
                    Why this course?
                </span>

                <p class="explanation-text">
                    ${escapeHtml(explanation)}
                </p>

            </div>


            <div class="recommendation-footer">

                <a
                    href="course-details.html?id=${encodeURIComponent(courseId)}"
                    class="btn btn-secondary course-details-btn"
                >
                    View Course
                </a>

            </div>

        </article>
    `;
}


/* =========================================
   COUNT
========================================= */

function updateRecommendationCount() {

    const element =
        document.getElementById(
            "recommendationCount"
        );

    if (!element) {
        return;
    }

    element.textContent =
        currentRecommendations.length;
}


/* =========================================
   STATES
========================================= */

function showLoading() {

    const loading =
        document.getElementById(
            "loadingState"
        );

    const empty =
        document.getElementById(
            "emptyState"
        );

    const grid =
        document.getElementById(
            "recommendationGrid"
        );

    if (loading) {
        loading.style.display = "block";
    }

    if (empty) {
        empty.style.display = "none";
    }

    if (grid) {
        grid.innerHTML = "";
    }

}


function showEmptyState(message) {

    const loading =
        document.getElementById(
            "loadingState"
        );

    const empty =
        document.getElementById(
            "emptyState"
        );

    const grid =
        document.getElementById(
            "recommendationGrid"
        );

    if (loading) {
        loading.style.display = "none";
    }

    if (grid) {
        grid.innerHTML = "";
    }

    if (empty) {

        empty.style.display = "block";

        const paragraph =
            empty.querySelector("p");

        if (paragraph) {
            paragraph.textContent = message;
        }

    }

}


/* =========================================
   HELPERS
========================================= */

function setText(id, value) {

    const element =
        document.getElementById(id);

    if (element) {
        element.textContent = value;
    }

}