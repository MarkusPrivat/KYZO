# 🦎 KYZO: Next-Gen Education

## Lernen, das sich dir anpasst. Schlauer lernen mit deinem AI-Buddy.


## How to Install?

To set up the project locally, follow these steps.

1. **Clone the Repository**:
   ```bash
   git clone git@github.com:MarkusPrivat/KYZO.git  
   cd KYZO 
   ```  
2. **Install dependencies**:  
   ```bash  
   pip install -r requirements.txt  
   ```  
3. **Configure Enviroment**:<br>
Copy `apps/kyzo_backend/.env_template` to `.env` and add your key:
   ```plaintext
   OPENAI_API_KEY=your_openai_key
   ```
4. **Run the backend application**:
   ```bash  
   python apps/kyzo_backend/run_backend.py
   ```

## 📖 Database Dependencies & Order of Creation

To ensure data integrity and avoid Foreign Key constraints, data should be created in the following hierarchical order:

1. **Users**: Can always be registered independently.
2. **Subjects**: Can be created independently (e.g., "History", "Math").
3. **Topics**: Require a valid `subject_id` to be linked to a specific subject.
4. **Question Inputs**: Require a `user_id`, `subject_id`, and `topic_id`. This is the "container" for the raw text and AI drafts.
5. **Questions**: Created from a `question_input`. They are linked to the input via the `question_origins` table to maintain traceability.

### Tip for Testing:
If you are testing with a fresh database, make sure to create at least one User, one Subject, and one Topic via the Swagger UI
👉 http://127.0.0.1:8000/docs