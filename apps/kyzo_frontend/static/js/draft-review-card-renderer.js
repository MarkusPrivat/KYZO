/**
 * Draft Review Card Renderer
 * Renders individual Draft-Fragen as cards with options, correct markers,
 * explanations, and difficulty/grade badges.
 *
 * Public API:
 *   renderCard(question) → HTMLElement
 *
 * Usage:
 *   var card = renderCard(questionObject);
 *   document.getElementById('container').appendChild(card);
 */

/* ── Card rendering ──────────────────────────────────────────────────────── */

/**
 * Render a single Draft-Frage as a card HTMLElement.
 * @param {Object} question - QuestionInputExtractedQuestions object
 * @returns {HTMLElement}
 */
function renderCard(question) {
    /**
     * Escape HTML special characters to prevent XSS.
     * @param {string} text
     * @returns {string}
     */
    function escapeHtml(text) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(text));
        return div.innerHTML;
    }

    var card = document.createElement('div');
    card.className = 'draft-card';

    // ── Body ──────────────────────────────────────────────────────────────

    var body = document.createElement('div');
    body.className = 'draft-card__body';

    // Question text
    var questionText = document.createElement('div');
    questionText.className = 'draft-card__question-text';
    questionText.textContent = question.question_text || '';
    body.appendChild(questionText);

    // Options list
    var optionsList = document.createElement('div');
    optionsList.className = 'draft-card__options';

    if (question.options && question.options.length > 0) {
        for (var i = 0; i < question.options.length; i++) {
            var option = question.options[i];
            var optionEl = document.createElement('div');
            optionEl.className = 'draft-card__option';

            if (option.is_correct) {
                optionEl.classList.add('draft-card__option--correct');
            }

            var optionText = document.createElement('div');
            optionText.className = 'draft-card__option-text';
            optionText.textContent = option.answer || '';
            optionEl.appendChild(optionText);

            optionsList.appendChild(optionEl);
        }
    }

    body.appendChild(optionsList);

    // Explanation (directly after correct answer, not collapsible)
    if (question.explanations && question.explanations.length > 0) {
        var explanationEl = document.createElement('div');
        explanationEl.className = 'draft-card__explanation';
        explanationEl.textContent = question.explanations[0].explanation || '';
        body.appendChild(explanationEl);
    }

    card.appendChild(body);

    // ── Footer (badges) ───────────────────────────────────────────────────

    var footer = document.createElement('div');
    footer.className = 'draft-card__footer';

    if (question.difficulty != null) {
        var difficultyBadge = document.createElement('span');
        difficultyBadge.className = 'draft-card__badge draft-card__badge--difficulty';
        difficultyBadge.textContent = 'Difficulty: ' + question.difficulty;
        footer.appendChild(difficultyBadge);
    }

    if (question.grade != null) {
        var gradeBadge = document.createElement('span');
        gradeBadge.className = 'draft-card__badge draft-card__badge--grade';
        gradeBadge.textContent = 'Grade: ' + question.grade;
        footer.appendChild(gradeBadge);
    }

    card.appendChild(footer);

    return card;
}
