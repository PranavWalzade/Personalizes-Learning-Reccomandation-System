(() => {
    "use strict";

    const API = "/api";
    const $ = (selector, root = document) => root.querySelector(selector);
    const app = $("#app");
    const studentId = () => localStorage.getItem("student_id");
    const state = {
        profile: null,
        courses: [],
        enrolled: [],
        skills: [],
        gaps: [],
        recommendations: [],
        learningPath: null,
        pathCourses: [],
        notifications: [],
        loadingError: ""
    };

    function escapeHtml(value) {
        return String(value ?? "").replace(/[&<>"']/g, (character) => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        })[character]);
    }

    async function api(endpoint, options = {}) {
        let response;
        try {
            response = await fetch(`${API}${endpoint}`, {
                method: options.method || "GET",
                headers: { "Content-Type": "application/json" },
                body: options.body === undefined
                    ? undefined
                    : JSON.stringify(options.body)
            });
        } catch (error) {
            throw new Error("Cannot reach LearnAI. Make sure the backend server is running.");
        }

        let result;
        try {
            result = await response.json();
        } catch (error) {
            throw new Error("The server returned an invalid response.");
        }

        if (!response.ok) {
            throw new Error(result.message || result.error || `Request failed (${response.status}).`);
        }

        return result;
    }

    const get = (endpoint) => api(endpoint);
    const post = (endpoint, body = {}) => api(endpoint, { method: "POST", body });
    const put = (endpoint, body = {}) => api(endpoint, { method: "PUT", body });
    const remove = (endpoint) => api(endpoint, { method: "DELETE" });
    const sid = () => encodeURIComponent(studentId());
    const studentEndpoint = (resource) => `/student/${sid()}/${resource}`;

    function pageKey() {
        const filename = location.pathname.split("/").pop().replace(/\.html$/, "");
        return ({
            "index": "home",
            "course-details": "courses"
        })[filename] || filename || "home";
    }

    function link(page, label, classes = "text-link") {
        return `<a class="${classes}" href="/pages/${page}.html">${label}</a>`;
    }

    function messageBox(message, type = "error") {
        return `<div class="message ${type}" role="status">${escapeHtml(message)}</div>`;
    }

    function formatDate(value) {
        if (!value) return "Not available";
        const date = new Date(value);
        return Number.isNaN(date.getTime()) ? "Not available" : date.toLocaleDateString();
    }

    function normalize(value) {
        return String(value || "").trim().toLowerCase();
    }

    async function loadCatalog() {
        const result = await get("/courses");
        state.courses = result.courses || [];
    }

    async function loadWorkspace(page) {
        const profileResult = await get(`/profile/${sid()}`);
        const [coursesResult, enrolledResult, skillsResult] = await Promise.all([
            get("/courses"),
            get(studentEndpoint("courses")),
            get(studentEndpoint("skills"))
        ]);

        state.profile = profileResult.profile;
        state.courses = coursesResult.courses || [];
        state.enrolled = enrolledResult.courses || [];
        state.skills = skillsResult.skills || [];

        if (["dashboard", "skill-gaps", "learning-path"].includes(page)) {
            let gapResult = await get(studentEndpoint("skill-gaps"));
            state.gaps = gapResult.skill_gaps || [];

            if (!state.gaps.length) {
                gapResult = await post(studentEndpoint("skill-gaps/generate"));
                state.gaps = gapResult.skill_gaps || [];
            }

            const pathResult = await get(studentEndpoint("learning-path"));
            state.learningPath = pathResult.learning_path;
            state.pathCourses = pathResult.courses || [];

            if (!state.learningPath && state.gaps.length) {
                await post(studentEndpoint("learning-path/generate"));
                const generatedPath = await get(studentEndpoint("learning-path"));
                state.learningPath = generatedPath.learning_path;
                state.pathCourses = generatedPath.courses || [];
            }
        }

        if (page === "dashboard" || page === "notifications") {
            const notificationsResult = await get(studentEndpoint("notifications"));
            state.notifications = notificationsResult.notifications || [];
        }

        if (page === "recommendations" || page === "dashboard") {
            const branch = encodeURIComponent(state.profile.branch || "");
            const recommendationsResult = await get(
                `${studentEndpoint("recommendations")}?limit=10&branch=${branch}`
            );
            state.recommendations = recommendationsResult.recommendations || [];
        }
    }

    function logo() {
        return `<a class="brand" href="/"><span class="brand-mark">L</span><span>learn<em>ai</em></span></a>`;
    }

    function publicLanding() {
        document.title = "LearnAI - Personalized learning";
        return `<div class="landing">
            <header class="landing-nav">${logo()}<div class="nav-actions">
                ${link("login", "Sign in", "text-link")}
                ${link("register", "Create account", "btn btn-primary btn-small")}
            </div></header>
            <section class="landing-hero">
                <div class="hero-copy">
                    <span class="eyebrow">PERSONALIZED LEARNING</span>
                    <h1>Learn smarter.<br><span class="gradient-text">Learn your way.</span></h1>
                    <p>Explore your course catalog, discover recommendations from your learning profile, and follow a path built around your skill gaps.</p>
                    <div class="hero-actions">
                        ${link("register", "Create your account", "btn btn-primary")}
                        ${link("login", "I already have an account", "btn btn-outline")}
                    </div>
                </div>
                <div class="hero-art"><div class="orbital"><div class="orbital-small"></div><div class="orbital-core">AI</div><span class="orbit-tag tag1">Course catalog</span><span class="orbit-tag tag2">Skill insights</span><span class="orbit-tag tag3">Learning path</span></div></div>
            </section>
        </div>`;
    }

    function authPage(register) {
        document.title = register ? "Create account - LearnAI" : "Sign in - LearnAI";
        const branches = [...new Set(
            state.courses
                .map((course) => String(course.branch || "").trim())
                .filter((branch) => branch && normalize(branch) !== "all engineering")
        )].sort();
        return `<div class="auth-layout">
            <div class="auth-wrap">
                <aside class="auth-aside">${logo()}<div class="auth-quote">
                    <span class="eyebrow">YOUR LEARNING, YOUR WAY</span>
                    <h2>${register ? "Build your personalized learning space." : "Welcome back to your learning space."}</h2>
                    <p>Your account keeps your courses, recommendations, skills, and progress together.</p>
                </div></aside>
                <main class="auth-main">
                    <h1>${register ? "Create your account" : "Sign in"}</h1>
                    <p>${register ? "Tell us a little about your learning goals to get started." : "Sign in with your username or email address."}</p>
                    <div id="authMessage" aria-live="polite"></div>
                    <form id="${register ? "registerForm" : "loginForm"}">
                        ${register ? `
                            <div class="field"><label for="username">Username</label><input id="username" name="username" minlength="3" maxlength="100" autocomplete="username" required></div>
                            <div class="field"><label for="email">Email</label><input id="email" name="email" type="email" maxlength="150" autocomplete="email" required></div>
                            <div class="field"><label for="studentName">Full name</label><input id="studentName" name="student_name" maxlength="150" autocomplete="name" required></div>
                            <div class="field"><label for="branch">Engineering branch</label><select id="branch" name="branch" required><option value="">Select your branch</option>${branches.map((branch) => `<option value="${escapeHtml(branch)}">${escapeHtml(branch)}</option>`).join("")}</select></div>
                            <div class="field"><label for="semester">Current semester</label><select id="semester" name="semester" required><option value="">Select semester</option>${Array.from({ length: 8 }, (_, index) => `<option value="${index + 1}">Semester ${index + 1}</option>`).join("")}</select></div>
                            <div class="field"><label for="interests">Learning interests (optional)</label><input id="interests" name="interests" maxlength="500" placeholder="e.g. Python, machine learning, databases"></div>
                            <div class="field"><label for="difficulty">Preferred course difficulty</label><select id="difficulty" name="preferred_difficulty"><option value="1">1 - Introductory</option><option value="2">2 - Easy</option><option value="3" selected>3 - Intermediate</option><option value="4">4 - Challenging</option><option value="5">5 - Advanced</option></select></div>
                        ` : `
                            <div class="field"><label for="login">Username or email</label><input id="login" name="login" autocomplete="username" required></div>
                        `}
                        <div class="field"><label for="password">Password</label><input id="password" name="password" type="password" minlength="6" autocomplete="${register ? "new-password" : "current-password"}" required></div>
                        <button class="btn btn-primary btn-block" type="submit" id="authSubmit">${register ? "Create account" : "Sign in"}</button>
                    </form>
                    <p class="auth-small">${register ? `Already registered? ${link("login", "Sign in")}` : `New to LearnAI? ${link("register", "Create an account")}`}</p>
                </main>
            </div>
        </div>`;
    }

    function sidebar(page) {
        const name = state.profile?.student_name || "Learner";
        const items = [
            ["dashboard", "Overview"],
            ["courses", "Courses"],
            ["my-courses", "My courses"],
            ["recommendations", "Recommendations"],
            ["learning-path", "Learning path"],
            ["skill-gaps", "Skill gaps"],
            ["progress", "Progress"],
            ["profile", "My profile"]
        ];
        return `<aside class="sidebar">
            ${logo()}<div class="side-label">YOUR LEARNING</div>
            <nav class="side-nav">${items.map(([key, label]) =>
                `<a class="side-link ${page === key ? "active" : ""}" href="/pages/${key === "courses" ? "courses" : key}.html">${escapeHtml(label)}</a>`
            ).join("")}</nav>
            <div class="sidebar-bottom"><strong>${escapeHtml(name)}</strong><button class="btn btn-outline btn-small" type="button" data-action="logout">Sign out</button></div>
        </aside>`;
    }

    function shell(page, content) {
        const labels = {
            dashboard: "Overview",
            courses: "Courses",
            "my-courses": "My courses",
            recommendations: "Recommendations",
            "learning-path": "Learning path",
            "skill-gaps": "Skill gaps",
            progress: "Progress",
            profile: "My profile",
            notifications: "Notifications"
        };
        document.title = `${labels[page] || "LearnAI"} - LearnAI`;
        return `<div class="app-layout">${sidebar(page)}<main class="main">
            <header class="topbar"><div class="breadcrumbs"><a href="/pages/dashboard.html">LearnAI</a><span>›</span><b>${labels[page] || "LearnAI"}</b></div><div class="top-actions">${link("profile", escapeHtml(state.profile?.student_name || "My profile"), "text-link")}<button class="btn btn-outline btn-small" type="button" data-action="logout">Sign out</button></div></header>
            <div class="page" id="page">${content}<div class="footer-dash">LearnAI · Your learning data is saved to your account</div></div>
        </main></div>`;
    }

    function heading(title, description, action = "") {
        return `<div class="page-heading"><div><h1>${escapeHtml(title)}</h1><p>${escapeHtml(description)}</p></div>${action}</div>`;
    }

    function stat(label, value, detail) {
        return `<article class="glass stat-card"><div class="stat-label">${escapeHtml(label)}</div><div class="stat-value">${escapeHtml(value)}</div><div class="stat-foot">${escapeHtml(detail)}</div></article>`;
    }

    function courseCard(course, options = {}) {
        const code = String(course.course_id || "");
        const enrollment = state.enrolled.find((item) => item.course_id === code);
        const status = enrollment?.status;
        const action = !options.canEnroll
            ? (status === "completed"
                ? `<span class="tag green">Completed</span>`
                : `<button class="btn btn-outline btn-small" data-action="complete" data-course="${escapeHtml(code)}">Mark complete</button>`)
            : (enrollment
                ? `<div class="enrollment-actions">
                    <label class="enrollment-status">Status
                        <select data-course-status aria-label="Status for ${escapeHtml(course.course_name || code)}">
                            <option value="not_started" ${status === "not_started" ? "selected" : ""}>Not started</option>
                            <option value="in_progress" ${status === "in_progress" ? "selected" : ""}>In progress</option>
                            <option value="completed" ${status === "completed" ? "selected" : ""}>Completed</option>
                        </select>
                    </label>
                    <button class="btn btn-primary btn-small" data-action="update-course" data-course="${escapeHtml(code)}">Update course</button>
                    <button class="btn btn-outline btn-small" data-action="remove-course" data-course="${escapeHtml(code)}">Remove</button>
                </div>`
                : `<button class="btn btn-primary btn-small" data-action="enroll" data-course="${escapeHtml(code)}">Add course</button>`);
        const matchScore = course.hybrid_score === undefined
            ? ""
            : `<div class="course-match"><span>Recommended match</span><strong>${Math.round(Number(course.hybrid_score) * 100)}%</strong></div>${course.explanation ? `<p class="course-match-reason">${escapeHtml(course.explanation)}</p>` : ""}`;
        const progress = enrollment
            ? Math.max(0, Math.min(100, Math.round(Number(enrollment.progress_percent) || 0)))
            : 0;
        const progressSection = enrollment
            ? `<div class="course-progress"><div class="course-progress-label"><span>Course progress</span><strong>${progress}%</strong></div><div class="course-progress-track"><span style="width:${progress}%"></span></div></div>`
            : "";
        return `<article class="catalog-card course-card">
            <div class="catalog-body">
                <div class="course-card-heading">
                    <div class="course-tags"><span class="tag">${escapeHtml(course.category || course.branch || "Course")}</span><span class="tag green">Semester ${escapeHtml(course.semester || "-")}</span></div>
                    <span class="course-code">${escapeHtml(code)}</span>
                </div>
                <h3 class="course-title">${escapeHtml(course.course_name || course.title || code)}</h3>
                <p class="course-description">${escapeHtml(course.skills || course.description || "Course from the LearnAI catalog.")}</p>
                <div class="course-meta"><span>${escapeHtml(course.branch || "All branches")}</span><span>Difficulty ${escapeHtml(course.difficulty || "-")}</span></div>
                ${matchScore}
                ${progressSection}
                <div class="catalog-foot">${action}</div>
            </div>
        </article>`;
    }

    function noData(title, description, action = "") {
        return `<div class="empty-state"><h3>${escapeHtml(title)}</h3><p>${escapeHtml(description)}</p>${action}</div>`;
    }

    function relevantCourses() {
        const branch = normalize(state.profile?.branch);
        return state.courses.filter((course) => {
            const courseBranch = normalize(course.branch);
            return !branch || !courseBranch || courseBranch === branch || courseBranch === "all engineering" || courseBranch === "common";
        });
    }

    function dashboardPage() {
        const completed = state.enrolled.filter((course) => course.status === "completed").length;
        const inProgress = state.enrolled.filter((course) => course.status === "in_progress").length;
        const currentPath = state.pathCourses.slice(0, 3);
        const recs = state.recommendations.slice(0, 3);
        return `${heading(`Welcome, ${state.profile.student_name}`, "Your learning dashboard is connected to your account and course catalog.", link("profile", "Edit profile", "btn btn-outline btn-small"))}
            <div class="grid stats-grid">
                ${stat("Available courses", String(relevantCourses().length), `For ${state.profile.branch || "your profile"}`)}
                ${stat("My courses", String(state.enrolled.length), `${inProgress} in progress · ${completed} completed`)}
                ${stat("Skills tracked", String(state.skills.length), "Self-assessed skills")}
                ${stat("Skill gaps", String(state.gaps.length), "Generated from your course catalog")}
            </div>
            <div class="grid dash-grid">
                <section class="glass card"><div class="card-head"><div><h2>Recommended for you</h2><p>Ranked with the saved TF-IDF content model and your profile.</p></div>${link("recommendations", "View all", "text-link")}</div>
                    <div class="grid course-grid">${recs.length ? recs.map((item) => courseCard(item, { canEnroll: true })).join("") : noData("No recommendations yet", "Check that courses are loaded and add your interests in your profile.")}</div>
                </section>
                <section class="glass card"><div class="card-head"><div><h2>Your learning path</h2><p>Built from your current skill gaps.</p></div>${link("learning-path", "Open path", "text-link")}</div>
                    ${currentPath.length ? currentPath.map((course) => `<article class="learning-row"><span class="step-time">Step ${escapeHtml(course.sequence_number)}</span><h3>${escapeHtml(course.course_name)}</h3><p>${escapeHtml(course.skills || course.category || "")}</p></article>`).join("") : noData("No path generated yet", "Generate skill gaps to create your personalized path.", link("learning-path", "Open learning path", "btn btn-primary btn-small"))}
                </section>
            </div>`;
    }

    function coursesPage() {
        const courses = relevantCourses();
        return `${heading("Course catalog", `${courses.length} courses match your branch. Add a course to track your progress.`)}
            <div class="row-between" style="margin-bottom:14px"><input id="courseSearch" class="filter-input" type="search" placeholder="Search courses, skills, or categories" aria-label="Search courses"><span class="muted" id="courseCount">${courses.length} courses</span></div>
            <div class="grid course-grid" id="courseGrid">${courses.length ? courses.map((course) => courseCard(course, { canEnroll: true })).join("") : noData("No courses found", "The course catalog is empty. Load the engineering course catalog into the database.")}</div>`;
    }

    function myCoursesPage() {
        return `${heading("My courses", "Update course statuses or remove courses from your learning list.", link("courses", "Browse courses", "btn btn-primary btn-small"))}
            <div class="grid course-grid">${state.enrolled.length
                ? state.enrolled.map((course) => courseCard(course, { canEnroll: true })).join("")
                : noData("No courses added yet", "Add a course from the catalog to start tracking your learning.", link("courses", "Browse courses", "btn btn-primary btn-small"))}</div>`;
    }

    function recommendationsPage() {
        const results = state.recommendations;
        return `${heading("Recommendations", "Courses are ranked using your interests, skills, branch, and the trained TF-IDF model.")}
            <section class="glass card"><span class="eyebrow">TRAINED CONTENT MODEL</span><p class="muted">The saved TF-IDF vectorizer compares your profile with course topics. This is a content similarity score, not a guarantee of academic success.</p></section>
            <div class="grid course-grid">${results.length ? results.map((course) => courseCard(course, { canEnroll: true })).join("") : noData("No recommendations found", "Try adding interests to your profile or check the catalog and trained model.")}</div>`;
    }

    function skillGapsPage() {
        const rows = state.gaps.map((gap) => `<article class="skill-item">
            <span class="skill-name">${escapeHtml(gap.skill_name)}</span>
            <div class="progress-track"><div class="progress-bar" style="width:${Math.max(0, Math.min(100, Number(gap.current_level) || 0))}%"></div></div>
            <span class="skill-score">${Math.round(Number(gap.current_level) || 0)}% / ${Math.round(Number(gap.required_level) || 0)}%</span>
            <span class="tag">${escapeHtml(gap.priority)}</span>
        </article>`).join("");
        return `${heading("Skill gaps", "Compare your self-assessed skills with the requirements of courses in your branch.", `<button class="btn btn-outline btn-small" data-action="regenerate">Refresh analysis</button>`)}
            <section class="glass card"><div class="card-head"><div><h2>Your skill levels</h2><p>Add or update a skill to personalize the gap analysis.</p></div></div>
                <form id="skillForm" class="row-between" style="gap:10px;align-items:end;flex-wrap:wrap">
                    <div class="field"><label for="skillName">Skill</label><input id="skillName" name="skill_name" required maxlength="150" placeholder="e.g. Python"></div>
                    <div class="field"><label for="skillLevel">Current level (0-100)</label><input id="skillLevel" name="skill_level" type="number" min="0" max="100" value="0" required></div>
                    <button class="btn btn-primary btn-small" type="submit">Save skill</button>
                </form>
                ${state.skills.length ? `<div class="skill-list">${state.skills.map((skill) => `<article class="skill-item">
                    <span class="skill-name">${escapeHtml(skill.skill_name)}</span>
                    <input class="edit-skill-level" aria-label="${escapeHtml(skill.skill_name)} level" data-skill="${escapeHtml(skill.id)}" type="number" min="0" max="100" value="${Math.round(Number(skill.skill_level) || 0)}">
                    <span class="skill-score">%</span>
                    <button class="btn btn-outline btn-small" data-action="delete-skill" data-skill="${escapeHtml(skill.id)}">Remove</button>
                </article>`).join("")}</div>` : noData("No skills recorded", "Add your current skills above to see your gaps.")}</section>
            <section class="glass card"><div class="card-head"><div><h2>Skills to strengthen</h2><p>Current level compared with the highest course requirement found for each skill.</p></div></div>
                ${rows || noData("No current skill gaps", "Add courses to the catalog or update your self-assessed skills to refresh this analysis.")}</section>`;
    }

    function learningPathPage() {
        const courses = state.pathCourses;
        const content = courses.length
            ? `<div class="learning-path-list">${courses.map((course) => `<article class="learning-row">
                <span class="step-time">Step ${escapeHtml(course.sequence_number)} · ${escapeHtml(course.status)}</span>
                <h3>${escapeHtml(course.course_name)}</h3>
                <p>${escapeHtml(course.branch || "All branches")} · Semester ${escapeHtml(course.semester || "-")} · ${escapeHtml(course.skills || "")}</p>
            </article>`).join("")}</div>`
            : noData("Your learning path is not ready", state.gaps.length ? "No catalog courses matched the current skill gaps." : "No open skill gaps were found. Add skills or update your course catalog to build a path.");
        const details = state.learningPath
            ? `<div class="grid stats-grid">${stat("Courses", String(state.learningPath.total_courses), state.learningPath.path_name)}${stat("Estimated hours", String(state.learningPath.estimated_hours), "Based on course credits")}</div>`
            : "";
        return `${heading("Your learning path", "A sequence of courses chosen to address the most important gaps for your profile.", `<button class="btn btn-primary btn-small" data-action="regenerate">Generate path</button>`)}${details}<section class="glass card">${content}</section>`;
    }

    function profilePage() {
        const profile = state.profile;
        const branches = [...new Set(state.courses.map((course) => course.branch).filter((branch) => branch && normalize(branch) !== "all engineering"))].sort();
        return `${heading("My profile", "Keep your academic profile and interests up to date for better recommendations.")}
            <section class="glass card"><form id="profileForm">
                <div class="field"><label>Username</label><input value="${escapeHtml(profile.username)}" disabled></div>
                <div class="field"><label>Email</label><input value="${escapeHtml(profile.email)}" disabled></div>
                <div class="field"><label for="profileName">Full name</label><input id="profileName" name="student_name" value="${escapeHtml(profile.student_name)}" required maxlength="150"></div>
                <div class="field"><label for="profileBranch">Branch</label><select id="profileBranch" name="branch" required>${branches.map((branch) => `<option value="${escapeHtml(branch)}" ${branch === profile.branch ? "selected" : ""}>${escapeHtml(branch)}</option>`).join("")}</select></div>
                <div class="field"><label for="profileSemester">Semester</label><select id="profileSemester" name="semester">${Array.from({ length: 8 }, (_, index) => `<option value="${index + 1}" ${Number(profile.semester) === index + 1 ? "selected" : ""}>Semester ${index + 1}</option>`).join("")}</select></div>
                <div class="field"><label for="profileInterests">Interests</label><input id="profileInterests" name="interests" value="${escapeHtml(profile.interests || "")}" maxlength="500" placeholder="Python, data science, networking"></div>
                <div class="field"><label for="profileDifficulty">Preferred difficulty (1-5)</label><input id="profileDifficulty" name="preferred_difficulty" type="number" min="1" max="5" value="${escapeHtml(profile.preferred_difficulty || 3)}"></div>
                <button class="btn btn-primary" type="submit">Save profile</button>
            </form></section>`;
    }

    function progressPage() {
        const complete = state.enrolled.filter((course) => course.status === "completed").length;
        return `${heading("Your progress", "Progress is based on courses you have added to your account.")}
            <div class="grid stats-grid">${stat("Courses enrolled", String(state.enrolled.length), "Your course list")}${stat("Completed", String(complete), "Marked complete")}</div>
            <section class="glass card">${state.enrolled.length ? state.enrolled.map((course) => `<article class="learning-row"><h3>${escapeHtml(course.course_name)}</h3><p>${escapeHtml(course.status)} · ${escapeHtml(course.branch || "")}</p></article>`).join("") : noData("No course progress yet", "Add a course from the catalog to start learning.", link("courses", "Browse courses", "btn btn-primary btn-small"))}</section>`;
    }

    function notificationsPage() {
        return `${heading("Notifications", "Updates about your courses and learning activity.")}
            <section class="glass card">${state.notifications.length ? state.notifications.map((item) => `<article class="notification-item"><div><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.message)}</p><small>${formatDate(item.created_at)}</small></div></article>`).join("") : noData("No notifications", "Course and progress updates will appear here.")}</section>`;
    }

    function renderProtected(page) {
        const pages = {
            dashboard: dashboardPage,
            courses: coursesPage,
            "my-courses": myCoursesPage,
            recommendations: recommendationsPage,
            "skill-gaps": skillGapsPage,
            "learning-path": learningPathPage,
            profile: profilePage,
            progress: progressPage,
            notifications: notificationsPage
        };
        return shell(page, (pages[page] || dashboardPage)());
    }

    function showAuthMessage(text, success = false) {
        const element = $("#authMessage");
        if (element) element.innerHTML = messageBox(text, success ? "success" : "error");
    }

    function saveSession(user) {
        localStorage.setItem("user", JSON.stringify(user));
        localStorage.setItem("student_id", String(user.student_id));
    }

    function bindAuth(register) {
        const form = $(`#${register ? "registerForm" : "loginForm"}`);
        if (!form) return;
        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            const button = $("#authSubmit");
            button.disabled = true;
            button.textContent = register ? "Creating account..." : "Signing in...";
            try {
                const fields = new FormData(form);
                const result = await post(register ? "/register" : "/login", Object.fromEntries(fields.entries()));
                if (register) {
                    const profileResult = await get(`/profile/${result.student_id}`);
                    saveSession({
                        user_id: result.user_id,
                        student_id: result.student_id,
                        username: profileResult.profile.username,
                        email: profileResult.profile.email
                    });
                } else {
                    if (!result.user?.student_id) {
                        throw new Error("This account does not have a student profile.");
                    }
                    saveSession(result.user);
                }
                location.href = "/pages/dashboard.html";
            } catch (error) {
                showAuthMessage(error.message);
                button.disabled = false;
                button.textContent = register ? "Create account" : "Sign in";
            }
        });
    }

    async function reloadAndRender(page) {
        try {
            await loadWorkspace(page);
            app.innerHTML = renderProtected(page);
            bindProtected(page);
        } catch (error) {
            state.loadingError = error.message;
            app.innerHTML = shell(page, `${heading("Unable to load your learning data", "The backend reported an error while loading your account.")}${messageBox(error.message)}<button class="btn btn-outline" data-action="reload">Try again</button>`);
            bindProtected(page);
        }
    }

    async function regenerateInsights() {
        await post(studentEndpoint("skill-gaps/generate"));
        const gapResult = await get(studentEndpoint("skill-gaps"));
        state.gaps = gapResult.skill_gaps || [];
        if (state.gaps.length) {
            await post(studentEndpoint("learning-path/generate"));
        }
        await reloadAndRender(pageKey());
    }

    function bindProtected(page) {
        const search = $("#courseSearch");
        if (search) {
            search.addEventListener("input", () => {
                const query = normalize(search.value);
                const filtered = relevantCourses().filter((course) =>
                    normalize(`${course.course_name} ${course.course_id} ${course.skills} ${course.category}`).includes(query)
                );
                const grid = $("#courseGrid");
                const count = $("#courseCount");
                if (grid) grid.innerHTML = filtered.length
                    ? filtered.map((course) => courseCard(course, { canEnroll: true })).join("")
                    : noData("No matching courses", "Try a different search.");
                if (count) count.textContent = `${filtered.length} courses`;
            });
        }

        const skillForm = $("#skillForm");
        if (skillForm) skillForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const fields = new FormData(skillForm);
            try {
                await post(studentEndpoint("skills"), Object.fromEntries(fields.entries()));
                await regenerateInsights();
            } catch (error) {
                alert(error.message);
            }
        });

        const profileForm = $("#profileForm");
        if (profileForm) profileForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const fields = Object.fromEntries(new FormData(profileForm).entries());
            try {
                await put(`/profile/${sid()}`, fields);
                await reloadAndRender(page);
            } catch (error) {
                alert(error.message);
            }
        });

        const levelInputs = document.querySelectorAll(".edit-skill-level");
        levelInputs.forEach((input) => input.addEventListener("change", async () => {
            try {
                await put(`${studentEndpoint("skills")}/${encodeURIComponent(input.dataset.skill)}`, {
                    skill_level: input.value
                });
                await regenerateInsights();
            } catch (error) {
                alert(error.message);
            }
        }));

        app.onclick = async (event) => {
            const button = event.target.closest("[data-action]");
            if (!button) return;
            const action = button.dataset.action;
            try {
                if (action === "logout") {
                    localStorage.removeItem("user");
                    localStorage.removeItem("student_id");
                    location.href = "/pages/login.html";
                } else if (action === "reload") {
                    await reloadAndRender(page);
                } else if (action === "enroll") {
                    await post(studentEndpoint("courses"), {
                        course_id: button.dataset.course,
                        status: "in_progress"
                    });
                    await reloadAndRender(page);
                } else if (action === "complete") {
                    await put(`${studentEndpoint("courses")}/${encodeURIComponent(button.dataset.course)}`, {
                        status: "completed"
                    });
                    await reloadAndRender(page);
                } else if (action === "update-course") {
                    const courseCode = button.dataset.course;
                    const statusSelect = button.closest(".catalog-card")?.querySelector("[data-course-status]");
                    if (!courseCode || !(statusSelect instanceof HTMLSelectElement)) {
                        throw new Error("Course status could not be identified.");
                    }
                    button.disabled = true;
                    const result = await put(
                        `${studentEndpoint("courses")}/${encodeURIComponent(courseCode)}`,
                        { status: statusSelect.value }
                    );
                    if (!result.success) {
                        throw new Error(result.message || "Unable to update this course.");
                    }
                    await reloadAndRender(page);
                } else if (action === "remove-course") {
                    const courseCode = button.dataset.course;
                    if (!courseCode) {
                        throw new Error("Course could not be identified.");
                    }
                    const course = state.enrolled.find((item) => item.course_id === courseCode);
                    if (!window.confirm(`Remove "${course?.course_name || courseCode}" from My Courses? Its saved progress will also be removed.`)) {
                        return;
                    }
                    button.disabled = true;
                    const result = await remove(
                        `${studentEndpoint("courses")}/${encodeURIComponent(courseCode)}`
                    );
                    if (!result.success) {
                        throw new Error(result.message || "Unable to remove this course.");
                    }
                    await reloadAndRender(page);
                } else if (action === "delete-skill") {
                    await remove(`${studentEndpoint("skills")}/${encodeURIComponent(button.dataset.skill)}`);
                    await regenerateInsights();
                } else if (action === "regenerate") {
                    await regenerateInsights();
                }
            } catch (error) {
                if (button instanceof HTMLButtonElement) {
                    button.disabled = false;
                }
                alert(error.message);
            }
        };
    }

    async function start() {
        if (!app) return;
        const page = pageKey();

        if (page === "home") {
            if (studentId()) {
                location.replace("/pages/dashboard.html");
                return;
            }
            app.innerHTML = publicLanding();
            return;
        }

        if (page === "login" || page === "register") {
            if (studentId()) {
                location.replace("/pages/dashboard.html");
                return;
            }
            if (page === "register") {
                try {
                    await loadCatalog();
                } catch (error) {
                    app.innerHTML = `<div class="auth-layout"><main class="auth-main">${heading("Registration unavailable", "The course catalog could not be loaded.")}${messageBox(error.message)}</main></div>`;
                    return;
                }
            }
            app.innerHTML = authPage(page === "register");
            bindAuth(page === "register");
            return;
        }

        if (!studentId()) {
            location.replace("/pages/login.html");
            return;
        }

        await reloadAndRender(page);
    }

    start();
})();
