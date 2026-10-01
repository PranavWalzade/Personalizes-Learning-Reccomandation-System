let studentId = null;


/* =========================================
   PAGE START
========================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        studentId = getStudentId();

        if (!studentId) {
            return;
        }

        setupEvents();

        loadProfile();

        loadSkillGaps();

    }
);



/* =========================================
   EVENTS
========================================= */

function setupEvents() {

    const generateBtn =
        document.getElementById(
            "generateBtn"
        );


    const emptyGenerateBtn =
        document.getElementById(
            "emptyGenerateBtn"
        );


    generateBtn.addEventListener(
        "click",
        generateSkillGaps
    );


    emptyGenerateBtn.addEventListener(
        "click",
        generateSkillGaps
    );

}



/* =========================================
   PROFILE
========================================= */

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


        const branch =
            profile.branch ||
            "Engineering";


        document.getElementById(
            "userName"
        ).textContent = name;


        document.getElementById(
            "userBranch"
        ).textContent = branch;


        document.getElementById(
            "userAvatar"
        ).textContent =
            getInitials(name);

    }

    catch (error) {

        console.error(
            "Profile error:",
            error
        );

    }

}



/* =========================================
   LOAD SKILL GAPS
========================================= */

async function loadSkillGaps() {

    showLoading();

    hideError();


    try {

        const response =
            await apiGet(
                `/student/${studentId}/skill-gaps`
            );


        if (!response.success) {

            showError(
                response.message ||
                "Unable to load skill gaps."
            );

            showEmpty();

            return;
        }


        const gaps =
            response.skill_gaps || [];


        renderSkillGaps(gaps);

    }

    catch (error) {

        console.error(
            "Skill gap error:",
            error
        );


        showError(
            error.message ||
            "Unable to connect to the server."
        );


        showEmpty();

    }

    finally {

        hideLoading();

    }

}



/* =========================================
   GENERATE
========================================= */

async function generateSkillGaps() {

    const button =
        document.getElementById(
            "generateBtn"
        );


    const oldText =
        button.textContent;


    button.disabled = true;

    button.textContent =
        "⟳ Analyzing...";


    hideError();


    try {

        const response =
            await apiPost(
                `/student/${studentId}/skill-gaps/generate`,
                {}
            );


        if (!response.success) {

            showError(
                response.message ||
                "Unable to generate skill gaps."
            );

            return;
        }


        renderSkillGaps(
            response.skill_gaps || []
        );

    }

    catch (error) {

        console.error(
            "Generate skill gap error:",
            error
        );


        showError(
            error.message ||
            "Unable to generate skill analysis."
        );

    }

    finally {

        button.disabled = false;

        button.textContent =
            oldText;

    }

}



/* =========================================
   RENDER
========================================= */

function renderSkillGaps(gaps) {

    const container =
        document.getElementById(
            "skillGapsContainer"
        );


    const empty =
        document.getElementById(
            "emptyState"
        );


    container.innerHTML = "";


    updateSummary(gaps);


    if (!gaps.length) {

        container.style.display = "none";

        empty.style.display = "block";

        return;
    }


    container.style.display = "flex";

    empty.style.display = "none";


    gaps.forEach(
        function (gap) {

            container.appendChild(
                createGapCard(gap)
            );

        }
    );

}



/* =========================================
   SUMMARY
========================================= */

function updateSummary(gaps) {

    let high = 0;

    let medium = 0;

    let low = 0;


    gaps.forEach(
        function (gap) {

            const priority =
                String(
                    gap.priority || "medium"
                ).toLowerCase();


            if (priority === "high") {

                high++;

            }

            else if (priority === "low") {

                low++;

            }

            else {

                medium++;

            }

        }
    );


    document.getElementById(
        "totalGaps"
    ).textContent = gaps.length;


    document.getElementById(
        "highGaps"
    ).textContent = high;


    document.getElementById(
        "mediumGaps"
    ).textContent = medium;


    document.getElementById(
        "lowGaps"
    ).textContent = low;

}



/* =========================================
   CREATE GAP CARD
========================================= */

function createGapCard(gap) {

    const card =
        document.createElement(
            "article"
        );


    card.className =
        "skill-gap-card";


    const priority =
        String(
            gap.priority || "medium"
        ).toLowerCase();


    const priorityClass =
        priority === "high"
            ? "priority-high"
            : priority === "low"
                ? "priority-low"
                : "priority-medium";


    const current =
        Number(
            gap.current_level || 0
        );


    const required =
        Number(
            gap.required_level || 0
        );


    const gapScore =
        Number(
            gap.gap_score || 0
        );


    const gapPercentage =
        gapScore <= 1
            ? gapScore * 100
            : gapScore;


    card.innerHTML = `

        <div class="skill-gap-top">

            <div>

                <h3 class="skill-name">

                    ${escapeHtml(
                        gap.skill_name ||
                        "Unknown Skill"
                    )}

                </h3>

                <p class="skill-description">

                    Improve this skill to better match
                    the requirements of your learning path.

                </p>

            </div>


            <span
                class="priority-badge ${priorityClass}"
            >

                ${escapeHtml(
                    priority
                )}

            </span>

        </div>



        <div class="skill-levels">


            <div class="level-item">

                <div class="level-header">

                    <span>
                        Current Level
                    </span>

                    <strong>
                        ${formatNumber(
                            current,
                            1
                        )}%
                    </strong>

                </div>


                <div class="progress-track">

                    <div
                        class="progress-fill current-fill"
                        style="width:${Math.min(
                            current,
                            100
                        )}%"
                    ></div>

                </div>

            </div>



            <div class="level-item">

                <div class="level-header">

                    <span>
                        Required Level
                    </span>

                    <strong>
                        ${formatNumber(
                            required,
                            1
                        )}%
                    </strong>

                </div>


                <div class="progress-track">

                    <div
                        class="progress-fill required-fill"
                        style="width:${Math.min(
                            required,
                            100
                        )}%"
                    ></div>

                </div>

            </div>

        </div>



        <div class="gap-score-box">

            <span class="gap-score-label">
                Skill Gap
            </span>

            <span class="gap-score">

                ${formatNumber(
                    gapPercentage,
                    1
                )}%

            </span>

        </div>

    `;


    return card;

}



/* =========================================
   HELPERS
========================================= */

function getInitials(name) {

    return String(
        name || "Student"
    )
        .trim()
        .split(/\s+/)
        .slice(0, 2)
        .map(
            function (part) {
                return part.charAt(0);
            }
        )
        .join("")
        .toUpperCase();

}


function showLoading() {

    document.getElementById(
        "loadingState"
    ).style.display = "flex";

}


function hideLoading() {

    document.getElementById(
        "loadingState"
    ).style.display = "none";

}


function showEmpty() {

    document.getElementById(
        "skillGapsContainer"
    ).style.display = "none";


    document.getElementById(
        "emptyState"
    ).style.display = "block";

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


function hideError() {

    document.getElementById(
        "errorMessage"
    ).style.display =
        "none";

}