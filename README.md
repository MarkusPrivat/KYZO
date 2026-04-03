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

## 📖 Database Initialization & Seeding

To set up your local development environment with sample data, you can use the provided 
seeding script. This will create the database schema and populate it with initial users, 
subjects, topics, and question inputs.

How to Run:</br>
From the project root, execute the following command:
   ```bash  
   python apps/kyzo_backend/scripts/run_seeding.py
   ```

### Tip for Testing:
After seeding you can use the Swagger UI to create questions, tests etc.</br>
👉 http://127.0.0.1:8000/docs