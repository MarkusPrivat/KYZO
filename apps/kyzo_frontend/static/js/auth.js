   Registration
   ============================================ */
=======
/**
 * auth.js — Authentication utilities for Kyzo frontend.
 *
 * Handles client-side validation and API calls for user registration and login.
 */

   Register Page Initialization
   ============================================ */

document.addEventListener("DOMContentLoaded", function () {
  var form = document.getElementById("register-form");
=======
/* ============================================
   Get Auth Header
   ============================================ */

function getAuthHeader() {
  /**
   * Returns the Authorization header with the stored JWT token.
   *
   * @returns {Object} - Headers object with Bearer token.
   */
  var token = localStorage.getItem("jwt_token");
  if (token) {
    return { "Authorization": "Bearer " + token };
  }
  return {};
}

/* ============================================
   Register Page Initialization
   ============================================ */

document.addEventListener("DOMContentLoaded", function () {
  var form = document.getElementById("register-form");============================================
   Login
   ============================================ */

function login(username, password) {
  /**
   * Sends login credentials to the backend API.
   *
   * @param {string} username - User's email address.
   * @param {string} password - User's password.
   * @returns {Promise<Object>} - The response from the API.
   */
  var body = "username=" + encodeURIComponent(username) + "&password=" + encodeURIComponent(password);

  return fetch(API_URL + "/users/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: body,
  }).then(function (response) {
    if (response.status === 200) {
      return response.json().then(function (data) {
        localStorage.setItem("jwt_token", data.token);
        return { token: data.token };
      });
    }
    if (response.status === 401) {
      return response.json().then(function (data) {
        var error = data.detail || "E-Mail oder Passwort ist falsch.";
        return { error: error, field: "email" };
      });
    }
    return response.json().then(function (data) {
      return { error: data.detail || "Ein Fehler ist aufgetreten." };
    });
  });
}

/* ============================================
   Registration
   ============================================ */============================================
   Registration
   ============================================ */

function register(formData) {
  /**
   * Sends registration data to the backend API.
   *
   * @param {Object} formData - Form data containing name, email, password, grade.
   * @returns {Promise<Object>} - The response from the API.
   */
  return fetch(API_URL + "/users/register-user", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(formData),
  }).then(function (response) {
    if (response.status === 201) {
      return response.json().then(function (data) {
        window.location.href = "/login";
        return data;
      });
    }
    if (response.status === 409) {
      return response.json().then(function (data) {
        var error = data.detail || "Diese E-Mail-Adresse ist bereits registriert.";
        return { error: error, field: "email" };
      });
    }
    return response.json().then(function (data) {
      return { error: data.detail || "Ein Fehler ist aufgetreten." };
    });
  });
}

/* ============================================
   Register Page Initialization
   ============================================ */

document.addEventListener("DOMContentLoaded", function () {
  var form = document.getElementById("register-form");
  if (!form) {
    return;
  }

  var nameInput = document.getElementById("register-name");
  var emailInput = document.getElementById("register-email");
  var passwordInput = document.getElementById("register-password");
  var gradeSelect = document.getElementById("register-grade");
  var submitBtn = document.getElementById("register-submit");
  var btnText = document.getElementById("register-btn-text");
  var spinner = document.getElementById("register-spinner");
  var globalError = document.getElementById("register-global-error");

  /* --- Validation helpers --- */

  function validateName(value) {
    if (!value || value.trim().length < 3) {
      return "Name muss mindestens 3 Zeichen lang sein.";
    }
    if (value.length > 100) {
      return "Name darf maximal 100 Zeichen lang sein.";
    }
    return "";
  }

  function validateEmail(value) {
    if (!value) {
      return "E-Mail ist ein Pflichtfeld.";
    }
    var emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(value)) {
      return "Bitte gib eine gültige E-Mail-Adresse ein.";
    }
    return "";
  }

  function validatePassword(value) {
    if (!value || value.length < 8) {
      return "Passwort muss mindestens 8 Zeichen lang sein.";
    }
    return "";
  }

  function validateGrade(value) {
    if (!value) {
      return "Bitte wähle ein Schuljahr aus.";
    }
    return "";
  }

  /* --- Inline error display --- */

  function showError(inputEl, errorEl, message) {
    if (message) {
      errorEl.textContent = message;
      inputEl.setAttribute("aria-invalid", "true");
    } else {
      errorEl.textContent = "";
      inputEl.removeAttribute("aria-invalid");
    }
  }

  function clearError(errorEl) {
    errorEl.textContent = "";
  }

  function showGlobalError(message) {
    globalError.textContent = message;
    globalError.removeAttribute("hidden");
  }

  function clearGlobalError() {
    globalError.textContent = "";
    globalError.setAttribute("hidden", "");
  }

  /* --- Real-time validation on blur --- */

  nameInput.addEventListener("blur", function () {
    var error = validateName(nameInput.value);
    showError(nameInput, document.getElementById("register-name-error"), error);
  });

  emailInput.addEventListener("blur", function () {
    var error = validateEmail(emailInput.value);
    showError(emailInput, document.getElementById("register-email-error"), error);
  });

  passwordInput.addEventListener("blur", function () {
    var error = validatePassword(passwordInput.value);
    showError(passwordInput, document.getElementById("register-password-error"), error);
  });

  gradeSelect.addEventListener("blur", function () {
    var error = validateGrade(gradeSelect.value);
    showError(gradeSelect, document.getElementById("register-grade-error"), error);
  });

  /* --- Clear errors on input --- */

  nameInput.addEventListener("input", function () {
    clearError(document.getElementById("register-name-error"));
  });

  emailInput.addEventListener("input", function () {
    clearError(document.getElementById("register-email-error"));
  });

  passwordInput.addEventListener("input", function () {
    clearError(document.getElementById("register-password-error"));
  });

  gradeSelect.addEventListener("change", function () {
    clearError(document.getElementById("register-grade-error"));
  });

  /* --- Form submission --- */

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    clearGlobalError();

    var nameError = validateName(nameInput.value);
    var emailError = validateEmail(emailInput.value);
    var passwordError = validatePassword(passwordInput.value);
    var gradeError = validateGrade(gradeSelect.value);

    showError(nameInput, document.getElementById("register-name-error"), nameError);
    showError(emailInput, document.getElementById("register-email-error"), emailError);
    showError(passwordInput, document.getElementById("register-password-error"), passwordError);
    showError(gradeSelect, document.getElementById("register-grade-error"), gradeError);

    if (nameError || emailError || passwordError || gradeError) {
      return;
    }

    /* Disable button and show spinner */
    submitBtn.disabled = true;
    btnText.setAttribute("hidden", "");
    spinner.removeAttribute("hidden");

    var formData = {
      name: nameInput.value.trim(),
      email: emailInput.value.trim(),
      password: passwordInput.value,
      grade: parseInt(gradeSelect.value, 10),
    };

    register(formData).then(function (result) {
      if (result.error) {
        /* Restore button */
        submitBtn.disabled = false;
        btnText.removeAttribute("hidden");
        spinner.setAttribute("hidden", "");

        if (result.field) {
          showError(
            document.getElementById("register-" + result.field),
            document.getElementById("register-" + result.field + "-error"),
            result.error
          );
        } else {
          showGlobalError(result.error);
        }
      }
      /* On success (201), register() redirects — no button restore needed */
    }).catch(function () {
      /* Restore button on network error */
      submitBtn.disabled = false;
      btnText.removeAttribute("hidden");
      spinner.setAttribute("hidden", "");
      showGlobalError("Verbindungsfehler. Bitte versuche es später erneut.");
    });
  });
});

/* ============================================
   Login Page Initialization
   ============================================ */

document.addEventListener("DOMContentLoaded", function () {
  var form = document.getElementById("login-form");
  if (!form) {
    return;
  }

  var emailInput = document.getElementById("login-email");
  var passwordInput = document.getElementById("login-password");
  var submitBtn = document.getElementById("login-submit");
  var btnText = document.getElementById("login-btn-text");
  var spinner = document.getElementById("login-spinner");
  var globalError = document.getElementById("login-global-error");

  /* --- Validation helpers --- */

  function validateEmail(value) {
    if (!value) {
      return "E-Mail ist ein Pflichtfeld.";
    }
    var emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(value)) {
      return "Bitte gib eine gültige E-Mail-Adresse ein.";
    }
    return "";
  }

  function validatePassword(value) {
    if (!value) {
      return "Passwort ist ein Pflichtfeld.";
    }
    if (value.length < 8) {
      return "Passwort muss mindestens 8 Zeichen lang sein.";
    }
    return "";
  }

  /* --- Inline error display --- */

  function showError(inputEl, errorEl, message) {
    if (message) {
      errorEl.textContent = message;
      inputEl.setAttribute("aria-invalid", "true");
    } else {
      errorEl.textContent = "";
      inputEl.removeAttribute("aria-invalid");
    }
  }

  function clearError(errorEl) {
    errorEl.textContent = "";
  }

  function showGlobalError(message) {
    globalError.textContent = message;
    globalError.removeAttribute("hidden");
  }

  function clearGlobalError() {
    globalError.textContent = "";
    globalError.setAttribute("hidden", "");
  }

  /* --- Real-time validation on blur --- */

  emailInput.addEventListener("blur", function () {
    var error = validateEmail(emailInput.value);
    showError(emailInput, document.getElementById("login-email-error"), error);
  });

  passwordInput.addEventListener("blur", function () {
    var error = validatePassword(passwordInput.value);
    showError(passwordInput, document.getElementById("login-password-error"), error);
  });

  /* --- Clear errors on input --- */

  emailInput.addEventListener("input", function () {
    clearError(document.getElementById("login-email-error"));
  });

  passwordInput.addEventListener("input", function () {
    clearError(document.getElementById("login-password-error"));
  });

  /* --- Form submission --- */

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    clearGlobalError();

    var emailError = validateEmail(emailInput.value);
    var passwordError = validatePassword(passwordInput.value);

    showError(emailInput, document.getElementById("login-email-error"), emailError);
    showError(passwordInput, document.getElementById("login-password-error"), passwordError);

    if (emailError || passwordError) {
      return;
    }

    /* Disable button and show spinner */
    submitBtn.disabled = true;
    btnText.setAttribute("hidden", "");
    spinner.removeAttribute("hidden");

    login(emailInput.value.trim(), passwordInput.value).then(function (result) {
      if (result.error) {
        /* Restore button */
        submitBtn.disabled = false;
        btnText.removeAttribute("hidden");
        spinner.setAttribute("hidden", "");

        if (result.field) {
          showError(
            document.getElementById("login-" + result.field),
            document.getElementById("login-" + result.field + "-error"),
            result.error
          );
        } else {
          showGlobalError(result.error);
        }
      }
      /* On success (200), redirect to home */
      if (result.token) {
        window.location.href = "/";
      }
    }).catch(function () {
      /* Restore button on network error */
      submitBtn.disabled = false;
      btnText.removeAttribute("hidden");
      spinner.setAttribute("hidden", "");
      showGlobalError("Verbindungsfehler. Bitte versuche es später erneut.");
    });
  });
});
