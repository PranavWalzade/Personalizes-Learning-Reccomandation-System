const studentId = getStudentId();

let dashboardLoading = false;
let dashboardRefreshPending = false;

if (studentId) {
    loadDashboard();

    window.addEventListener(
        "learnai:data-changed",
        refreshDashboardAfterChange
    );

    window.addEventListener(
        "storage",
        function (event) {
            if (event.key === "learnai:data-changed") {
                refreshDashboardAfterChange();
            }
        }
    );

    window.addEventListener(
        "focus",
        refreshDashboardAfterChange
    );

    document.addEventListener(
        "visibilitychange",
        function () {
            if (!document.hidden) {
                refreshDashboardAfterChange();
            }
        }
    );

    window.setInterval(function () {
        if (!document.hidden) {
            loadDashboard(false);
        }
    }, 30000);
}

function refreshDashboardAfterChange() {
    if (!document.hidden) {
        loadDashboard(false);
    }
}


async function loadDashboard(showLoading = true) {

    if (dashboardLoading) {
        dashboardRefreshPending = true;
        return;
    }

    dashboardLoading = true;

    try {
        if (showLoading) {
            showDashboardLoading();
        }

        const response = await apiGet(
            `/dashboard/${studentId}`
        );

        if (!response.success) {
            throw new Error(
                response.message || "Failed to load dashboard"
            );
        }

        const data = response.data || response;

        renderProfile(data);
        renderStats(data);
        renderLearningProfile(data);
        renderSkillGaps(data);
        renderNotifications(data);

        await loadRecommendations();
        hideDashboardError();

    } catch (error) {
        console.error(
            "Dashboard error:",
            error
        );

        showDashboardError(
            error.message
        );

    } finally {
        dashboardLoading = false;

        if (dashboardRefreshPending) {
            dashboardRefreshPending = false;
            loadDashboard(false);
        }
    }
}


function renderProfile(data) {

    const profile =
        data.student ||
        data.profile ||
        data.student_profile ||
        {};

    const name =
        profile.student_name ||
        profile.name ||
        "Student";

    const branch =
        profile.branch ||
        "Engineering";

    const semester =
        profile.semester ||
        "-";

    const welcomeElement =
        document.getElementById(
            "welcomeName"
        );

    const branchElement =
        document.getElementById(
            "studentBranch"
        );

    const semesterElement =
        document.getElementById(
            "studentSemester"
        );

    if (welcomeElement) {
        welcomeElement.textContent =
            name;
    }

    setText("topbarName", name);
    setText("profileName", name);

    if (branchElement) {
        branchElement.textContent =
            formatText(branch);
    }

    if (semesterElement) {
        semesterElement.textContent =
            `Semester ${semester}`;
    }

    const avatar =
        document.getElementById(
            "studentAvatar"
        );

    if (avatar) {
        avatar.textContent =
            name.charAt(0).toUpperCase();
    }

    setText(
        "topbarAvatar",
        name.charAt(0).toUpperCase()
    );
}


function renderStats(data) {

    const courseStats =
        data.course_stats ||
        data.stats ||
        data.courses ||
        {};

    const progressStats =
        data.progress_stats ||
        data.progress ||
        {};

    const skillCount =
        data.skill_count ??
        data.skills_count ??
        courseStats.skill_count ??
        progressStats.skill_count ??
        0;

    const totalCourses =
        courseStats.total ??
        courseStats.total_courses ??
        0;

    const completedCourses =
        courseStats.completed ??
        courseStats.completed_courses ??
        0;

    const progress =
        progressStats.average_progress ??
        progressStats.avg_progress ??
        progressStats.progress_percent ??
        courseStats.average_progress ??
        0;

    setText(
        "totalCourses",
        totalCourses
    );

    setText(
        "completedCourses",
        completedCourses
    );

    setText(
        "skillCount",
        skillCount
    );

    setText(
        "averageProgress",
        `${formatNumber(progress, 0)}%`
    );
}


function renderLearningProfile(data) {

    const profile =
        data.student ||
        data.profile ||
        data.student_profile ||
        {};

    const academic =
        toPercentage(
            profile.academic_strength
        );

    const engagement =
        toPercentage(
            profile.engagement_strength
        );

    const readiness =
        toPercentage(
            profile.readiness_score
        );

    setText(
        "academicValue",
        `${formatNumber(academic, 0)}%`
    );

    setText(
        "engagementValue",
        `${formatNumber(engagement, 0)}%`
    );

    setText(
        "readinessValue",
        `${formatNumber(readiness, 0)}%`
    );

    setText(
        "learningReadinessValue",
        `${formatNumber(readiness, 0)}%`
    );

    setWidth(
        "academicBar",
        academic
    );

    setWidth(
        "engagementBar",
        engagement
    );

    setWidth(
        "readinessBar",
        readiness
    );

    setText(
        "learningLevel",
        formatText(
            profile.learning_level ||
            "Not Available"
        )
    );
}


function renderSkillGaps(data) {

    const gaps =
        data.top_skill_gaps ||
        data.skill_gaps ||
        [];

    const container =
        document.getElementById(
            "dashboardSkillGaps"
        );

    if (!container) {
        return;
    }

    if (!Array.isArray(gaps) ||
        gaps.length === 0) {

        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">
                    ✓
                </div>

                <h3>No skill gaps found</h3>

                <p>
                    Generate your skill analysis
                    to identify areas for improvement.
                </p>

                <a
                    href="skill-gaps.html"
                    class="btn btn-primary"
                >
                    Analyze Skills
                </a>
            </div>
        `;

        return;
    }

    container.innerHTML =
        gaps.slice(0, 5)
        .map(function (gap) {

            const skill =
                escapeHtml(
                    gap.skill_name ||
                    gap.skill ||
                    "Unknown Skill"
                );

            const gapScore =
                Number(
                    gap.gap_score ??
                    gap.gap ??
                    0
                );

            const percentage =
                gapScore <= 1
                    ? gapScore * 100
                    : gapScore;

            const priority =
                formatText(
                    gap.priority ||
                    "medium"
                );

            return `
                <div class="dashboard-gap-item">

                    <div class="dashboard-gap-header">

                        <span>
                            ${skill}
                        </span>

                        <span class="badge badge-${priority.toLowerCase()}">
                            ${priority}
                        </span>

                    </div>

                    <div class="progress-track">

                        <div
                            class="progress-fill"
                            style="width:${Math.min(
                                percentage,
                                100
                            )}%"
                        ></div>

                    </div>

                    <small>
                        Gap:
                        ${formatNumber(
                            percentage,
                            0
                        )}%
                    </small>

                </div>
            `;
        })
        .join("");
}


function renderNotifications(data) {

    const notifications =
        data.notifications ||
        [];

    const container =
        document.getElementById(
            "dashboardNotifications"
        );

    if (!container) {
        return;
    }

    if (!Array.isArray(notifications) ||
        notifications.length === 0) {

        container.innerHTML = `
            <div class="empty-state compact">
                <div class="empty-state-icon">
                    ✓
                </div>

                <p>
                    No new notifications.
                </p>
            </div>
        `;

        return;
    }

    container.innerHTML =
        notifications
        .slice(0, 5)
        .map(function (notification) {

            const title =
                escapeHtml(
                    notification.title ||
                    "Notification"
                );

            const message =
                escapeHtml(
                    notification.message ||
                    ""
                );

            const isRead =
                Number(
                    notification.is_read
                ) === 1;

            return `
                <div class="
                    dashboard-notification-item
                    ${isRead ? "read" : "unread"}
                ">

                    <div class="notification-dot"></div>

                    <div>

                        <h4>
                            ${title}
                        </h4>

                        <p>
                            ${message}
                        </p>

                    </div>

                </div>
            `;
        })
        .join("");
}


async function loadRecommendations() {

    const container =
        document.getElementById(
            "dashboardRecommendations"
        );

    if (!container) {
        return;
    }

    try {

        const response =
            await apiGet(
                `/student/${studentId}/recommendations?limit=3`
            );

        const recommendations =
            response.recommendations ||
            response.data?.recommendations ||
            [];

        if (!Array.isArray(recommendations) ||
            recommendations.length === 0) {

            container.innerHTML = `
                <div class="empty-state">

                    <div class="empty-state-icon">
                        📚
                    </div>

                    <h3>
                        No recommendations yet
                    </h3>

                    <p>
                        Complete your profile to
                        receive personalized courses.
                    </p>

                    <a
                        href="recommendations.html"
                        class="btn btn-primary"
                    >
                        View Recommendations
                    </a>

                </div>
            `;

            return;
        }

        container.innerHTML =
            recommendations
            .map(function (item) {

                const courseName =
                    escapeHtml(
                        item.course_name ||
                        item.course?.course_name ||
                        "Course"
                    );

                const courseId =
                    escapeHtml(
                        item.course_id ||
                        item.course?.course_id ||
                        ""
                    );

                const branch =
                    escapeHtml(
                        item.branch ||
                        item.course?.branch ||
                        ""
                    );

                const score =
                    Number(
                        item.hybrid_score ||
                        item.score ||
                        0
                    );

                return `
                    <div class="dashboard-recommendation-card">

                        <div class="recommendation-rank">
                            #${item.rank || "-"}
                        </div>

                        <div class="recommendation-content">

                            <h3>
                                ${courseName}
                            </h3>

                            <p>
                                ${courseId}
                                ·
                                ${branch}
                            </p>

                            <div class="recommendation-score">

                                <span>
                                    AI Match
                                </span>

                                <strong>
                                    ${formatNumber(
                                        score * 100,
                                        0
                                    )}%
                                </strong>

                            </div>

                            <div class="progress-track">

                                <div
                                    class="progress-fill"
                                    style="width:${Math.min(
                                        score * 100,
                                        100
                                    )}%"
                                ></div>

                            </div>

                        </div>

                        <a
                            href="course-details.html?id=${courseId}"
                            class="btn btn-secondary"
                        >
                            View
                        </a>

                    </div>
                `;
            })
            .join("");

    } catch (error) {

        console.error(
            "Recommendation error:",
            error
        );

        container.innerHTML = `
            <div class="message error">
                Unable to load recommendations.
            </div>
        `;
    }
}


function toPercentage(value) {

    const number =
        Number(value);

    if (Number.isNaN(number)) {
        return 0;
    }

    if (number <= 1) {
        return number * 100;
    }

    return Math.min(
        number,
        100
    );
}


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
            value;
    }
}


function setWidth(
    elementId,
    value
) {

    const element =
        document.getElementById(
            elementId
        );

    if (element) {

        element.style.width =
            `${Math.min(
                Math.max(value, 0),
                100
            )}%`;
    }
}


function showDashboardLoading() {

    const containers = [
        "dashboardRecommendations",
        "dashboardSkillGaps",
        "dashboardNotifications"
    ];

    containers.forEach(function (id) {

        const element =
            document.getElementById(id);

        if (element) {

            element.innerHTML = `
                <div class="loading-state">
                    Loading...
                </div>
            `;
        }
    });
}


function showDashboardError(
    message
) {

    const element =
        document.getElementById("dashboardError");

    if (!element) {
        return;
    }

    element.textContent =
        message || "Unable to load dashboard";
    element.style.display = "block";
}


function hideDashboardError() {
    const element =
        document.getElementById("dashboardError");

    if (element) {
        element.style.display = "none";
        element.textContent = "";
    }
}