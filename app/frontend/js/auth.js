/* =========================================================
   LEARNAI AUTHENTICATION
========================================================= */


/* =========================================================
   PASSWORD TOGGLE
========================================================= */

function setupPasswordToggle(
    buttonId,
    inputId
) {

    const button =
        document.getElementById(buttonId);

    const input =
        document.getElementById(inputId);


    if (!button || !input) {
        return;
    }


    button.addEventListener(
        "click",
        function () {

            if (
                input.type === "password"
            ) {

                input.type = "text";

                button.textContent = "🙈";

                button.setAttribute(
                    "aria-label",
                    "Hide password"
                );

            } else {

                input.type = "password";

                button.textContent = "👁";

                button.setAttribute(
                    "aria-label",
                    "Show password"
                );
            }

        }
    );
}


/* =========================================================
   REGISTER
========================================================= */

function initializeRegister() {

    const form =
        document.getElementById(
            "registerForm"
        );


    if (!form) {
        return;
    }


    form.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            const message =
                document.getElementById(
                    "registerMessage"
                );


            const submitButton =
                document.getElementById(
                    "registerSubmit"
                );


            const username =
                document
                    .getElementById("username")
                    .value
                    .trim();


            const email =
                document
                    .getElementById("email")
                    .value
                    .trim();


            const password =
                document
                    .getElementById("password")
                    .value;


            const studentName =
                document
                    .getElementById("student_name")
                    .value
                    .trim();


            const branch =
                document
                    .getElementById("branch")
                    .value;


            const semester =
                Number(
                    document
                        .getElementById("semester")
                        .value
                );


            const interests =
                document
                    .getElementById("interests")
                    .value
                    .trim();


            const difficulty =
                Number(
                    document
                        .getElementById(
                            "preferred_difficulty"
                        )
                        .value
                );


            /* -----------------------------------------
               CLIENT VALIDATION
            ----------------------------------------- */

            if (
                username.length < 3
            ) {

                showAuthMessage(
                    message,
                    "Username must contain at least 3 characters.",
                    "error"
                );

                return;
            }


            if (
                password.length < 6
            ) {

                showAuthMessage(
                    message,
                    "Password must contain at least 6 characters.",
                    "error"
                );

                return;
            }


            if (
                !studentName
            ) {

                showAuthMessage(
                    message,
                    "Please enter your full name.",
                    "error"
                );

                return;
            }


            if (
                !branch
            ) {

                showAuthMessage(
                    message,
                    "Please select your engineering branch.",
                    "error"
                );

                return;
            }


            if (
                !semester ||
                semester < 1 ||
                semester > 8
            ) {

                showAuthMessage(
                    message,
                    "Please select a valid semester.",
                    "error"
                );

                return;
            }


            /* -----------------------------------------
               LOADING
            ----------------------------------------- */

            submitButton.disabled = true;

            submitButton.textContent =
                "Creating Account...";


            showAuthMessage(
                message,
                "Creating your account...",
                ""
            );


            /* -----------------------------------------
               REQUEST
            ----------------------------------------- */

            try {

                const data =
                    await apiPost(
                        "/register",
                        {
                            username:
                                username,

                            email:
                                email,

                            password:
                                password,

                            student_name:
                                studentName,

                            branch:
                                branch,

                            semester:
                                semester,

                            interests:
                                interests,

                            preferred_difficulty:
                                difficulty
                        }
                    );


                showAuthMessage(
                    message,
                    data.message ||
                    "Account created successfully.",
                    "success"
                );


                form.reset();


                setTimeout(
                    function () {

                        window.location.href =
                            "login.html";

                    },
                    1200
                );


            } catch (error) {

                console.error(
                    "Registration error:",
                    error
                );


                showAuthMessage(
                    message,
                    error.message ||
                    "Registration failed.",
                    "error"
                );

            } finally {

                submitButton.disabled =
                    false;

                submitButton.textContent =
                    "Create Account";
            }

        }
    );
}


/* =========================================================
   LOGIN
========================================================= */

function initializeLogin() {

    const form =
        document.getElementById(
            "loginForm"
        );


    if (!form) {
        return;
    }


    form.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            const message =
                document.getElementById(
                    "loginMessage"
                );


            const submitButton =
                document.getElementById(
                    "loginSubmit"
                );


            const login =
                document
                    .getElementById(
                        "loginIdentifier"
                    )
                    .value
                    .trim();


            const password =
                document
                    .getElementById(
                        "loginPassword"
                    )
                    .value;


            /* -----------------------------------------
               VALIDATION
            ----------------------------------------- */

            if (!login) {

                showAuthMessage(
                    message,
                    "Please enter your username or email.",
                    "error"
                );

                return;
            }


            if (!password) {

                showAuthMessage(
                    message,
                    "Please enter your password.",
                    "error"
                );

                return;
            }


            /* -----------------------------------------
               LOADING
            ----------------------------------------- */

            submitButton.disabled =
                true;

            submitButton.textContent =
                "Signing In...";


            showAuthMessage(
                message,
                "Signing you in...",
                ""
            );


            /* -----------------------------------------
               LOGIN REQUEST
            ----------------------------------------- */

            try {

                const data =
                    await apiPost(
                        "/login",
                        {
                            login:
                                login,

                            password:
                                password
                        }
                    );


                if (
                    !data.success
                ) {

                    throw new Error(
                        data.message ||
                        "Login failed."
                    );
                }


                const user =
                    data.user || {};


                const studentId =
                    user.student_id;


                if (!studentId) {

                    throw new Error(
                        "Login successful, but student profile was not found."
                    );
                }


                /* -----------------------------------------
                   SAVE SESSION
                ----------------------------------------- */

                localStorage.setItem(
                    "user",
                    JSON.stringify(user)
                );


                localStorage.setItem(
                    "student_id",
                    String(studentId)
                );


                showAuthMessage(
                    message,
                    "Login successful. Redirecting...",
                    "success"
                );


                setTimeout(
                    function () {

                        window.location.href =
                            "dashboard.html";

                    },
                    700
                );


            } catch (error) {

                console.error(
                    "Login error:",
                    error
                );


                showAuthMessage(
                    message,
                    error.message ||
                    "Invalid username/email or password.",
                    "error"
                );

            } finally {

                submitButton.disabled =
                    false;

                submitButton.textContent =
                    "Sign In";
            }

        }
    );
}


/* =========================================================
   MESSAGE
========================================================= */

function showAuthMessage(
    element,
    text,
    type
) {

    if (!element) {
        return;
    }


    element.className =
        "message";


    if (type) {

        element.classList.add(
            type
        );
    }


    element.textContent =
        text;
}


/* =========================================================
   INITIALIZE
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        setupPasswordToggle(
            "loginPasswordToggle",
            "loginPassword"
        );


        setupPasswordToggle(
            "registerPasswordToggle",
            "password"
        );


        initializeLogin();

        initializeRegister();

    }
);