# Issue: 0047 - Integrate Draft Review Page

## Meta & Context Capsule
- **Type**: AFK
- **Source PRD**: `/docs/intern/prd/done/002-draft-review.md`
- **Linked User Story**: [US-1] As a Teacher/Admin, I want to review the Draft-Fragen after generation to evaluate the quality of the AI output.
- **Linked User Story**: [US-6] As a Teacher/Admin, I want to adopt the Draft-Fragen into the global question pool via the Finalize button.
- **Linked User Story**: [US-7] As a Teacher/Admin, I want to see a notice when the input has already been finalized and not be able to click the Finalize button again.
- **Linked User Story**: [US-8] As a Teacher/Admin, I want to be automatically redirected to the Draft Review page after generating questions.
- **Linked User Story**: [US-10] As a Teacher/Admin, I want to resize the RAWInput-Accordion to read the text optimally.
- **Domain Vocabulary**: Refer to `/docs/intern/CONTEXT.md` for core terminology (QuestionInput, QuestionInputRAWInput, QuestionInputExtractedQuestions, Teacher, Admin).

## Parent Issue
None

## Blocked By
- `/docs/intern/issue-tracker/0045-implement-draft-review-card-renderer.md`
- `/docs/intern/issue-tracker/0046-implement-draft-review-polling.md`

## Architecture & ADR References
- **Applicable ADRs**: None
- **Target Module (Deep Module)**: DraftReviewPage

## What to Build (End-to-End Behavior)
Integrate the DraftReviewCardRenderer and DraftReviewPolling modules into the draft_review.html template. The page must:

1. **Load QuestionInput data**:
   - Fetch `GET /api/v1/questions/inputs/{question_input_id}` on page load
   - Display Metadaten (Subject, Topic, Grade, InputType, is_processed) at the top
   - Pass data to DraftReviewPolling for status monitoring

2. **RAWInput-Accordion**:
   - Collapsible section at the top of the page
   - Default state: collapsed
   - Resizable (user can adjust height)
   - Shows Dateiname/Größe/Typ for file uploads or full text for manual input
   - Displays source_ref and content from `raw_input`

3. **Draft-Fragen-Karten**:
   - Render all `extracted_questions` as cards using DraftReviewCardRenderer
   - Max. 25 questions, no pagination
   - Each card shows: question_text, options with is_correct marker, explanation after correct answer, difficulty/grade badges

4. **Finalize-Button**:
   - POST to `/api/v1/questions/inputs/{question_input_id}/finalize`
   - Disabled when `is_processed` is `true` with a notice "Dieser Input wurde bereits verarbeitet."
   - Shows spinner during API call
   - Displays toast on success: "X Fragen wurden in den Katalog übernommen."
   - Displays toast on error: "Fehler beim Finalize: [Grund]"

5. **Polling integration**:
   - Start polling when page loads
   - Show loading indicator while `is_processed` is `false`
   - Render Draft-Fragen-Karten when `is_processed` becomes `true`
   - Stop polling when complete

### Technical & Code References (From PRD)
- **Design-Pattern**: Aufbau auf `knowledge_topics.html` — bestehende CSS-Klassen (`admin-container`, `admin-sidebar`, `admin-nav`, `card`, `card-body`, `btn-primary`, `btn-secondary`, `toast`) werden wiederverwendet.
- **Navigation**: Neue Route `/admin/draft-review/<int:question_input_id>` in `admin.py` mit `teacher`/`admin`-Rollen-Check.
- **Navigation-Eintrag**: Neuer Link im Admin-Nav unter "Wissensverwaltung" — sichtbar für `teacher` und `admin`.
- **Toast-Nachrichten**: Erfolg: "X Fragen wurden in den Katalog übernommen." / Fehler: "Fehler beim Finalize: [Grund]".
- **RAWInput-Accordion**: Standardmäßig eingeklappt, resizable, zeigt Dateiname/Größe/Typ bei Upload oder vollen Text bei manuellem Input.
- **Max. 25 Fragen** pro Seite, keine Paginierung.
- **Kein Abbrechen-Button** — Navigation über Admin-Panel oder Browser-Back-Button.

### Prototype Snippets
**Page initialization flow:**
```javascript
document.addEventListener('DOMContentLoaded', function() {
    var questionInputId = parseInt(document.querySelector('.admin-draft-review').dataset.questionInputId);
    
    // Start polling
    DraftReviewPolling.startPolling(questionInputId, onReady, onInterval);
    
    function onReady(data) {
        // Render Metadaten
        renderMetadata(data);
        // Render RAWInput-Accordion
        renderRawInputAccordion(data.raw_input);
        // Render Draft-Fragen-Karten
        renderDraftCards(data.extracted_questions);
        // Setup Finalize-Button
        setupFinalizeButton(questionInputId, data.is_processed);
    }
    
    function onInterval() {
        // Update loading indicator
    }
});
```

**Finalize-Button handler:**
```javascript
function finalizeQuestionInput(questionInputId) {
    fetch(API_URL + '/questions/inputs/' + questionInputId + '/finalize', {
        method: 'POST',
        headers: getAuthHeader()
    })
    .then(function(response) {
        if (response.ok) {
            return response.json().then(function(data) {
                showToast('Fragen wurden in den Katalog übernommen.', 'success');
            });
        } else {
            return response.json().then(function(data) {
                showToast('Fehler beim Finalize: ' + (data.detail || 'Unbekannter Fehler'), 'error');
            });
        }
    })
    .catch(function(err) {
        showToast('Fehler beim Finalize: ' + err.message, 'error');
    });
}
```

## Acceptance Criteria
- [ ] **Functional:** Page loads QuestionInput data via GET `/api/v1/questions/inputs/{question_input_id}`
- [ ] **Functional:** Metadaten (Subject, Topic, Grade, InputType, is_processed) displayed at the top
- [ ] **Functional:** RAWInput-Accordion is collapsible, resizable, default collapsed
- [ ] **Functional:** Draft-Fragen-Karten rendered using DraftReviewCardRenderer (max. 25, no pagination)
- [ ] **Functional:** Finalize-Button calls POST `/api/v1/questions/inputs/{question_input_id}/finalize`
- [ ] **Functional:** Finalize-Button is disabled when `is_processed` is `true` with notice "Dieser Input wurde bereits verarbeitet."
- [ ] **Functional:** Toast success message: "X Fragen wurden in den Katalog übernommen."
- [ ] **Functional:** Toast error message: "Fehler beim Finalize: [Grund]"
- [ ] **Functional:** Polling shows loading indicator while `is_processed` is `false`
- [ ] **Functional:** Polling stops when `is_processed` becomes `true`
- [ ] **Functional:** No Abbrechen-Button — navigation via Admin-Panel or Browser-Back-Button
- [ ] **Technical:** Reuses existing CSS classes (`admin-container`, `admin-sidebar`, `admin-nav`, `card`, `card-body`, `btn-primary`, `btn-secondary`, `toast`)
- [ ] **Deep Interface:** DraftReviewCardRenderer and DraftReviewPolling integrated via their deep interfaces
- [ ] **Testing:** Integration tests cover full workflow: API-Call → Rendering → Finalize → Toast-Nachricht

## Guardrails & Operational Constraints
> [!IMPORTANT]
> - Do NOT close or modify any parent issue or referenced PRD files.
> - Do NOT guess missing technical details. If ambiguity arises, halt execution immediately (HITL-Trigger).
> - Specific file paths or custom code snippets outside of the specified prototype shapes are volatile and must not be introduced without verification.
