# ❤️ EmpathyPulse – AI-Powered Employee Sentiment Analyzer

EmpathyPulse is an intelligent web-based application designed to monitor and analyze employee sentiment through anonymous feedback. It leverages Natural Language Processing (NLP) to detect emotional states (such as stress, anger, happiness, or depression) and notifies HR in real time if negative sentiments are detected, helping organizations foster a healthier work environment.

---

## 🌟 Features

- 💬 Anonymous employee feedback submission  
- 🤖 AI-powered sentiment and emotion analysis using Hugging Face Transformers  
- 📈 Visual analytics and department-level sentiment trends (Plotly)  
- 🔐 Secure login/signup with bcrypt password hashing  
- 🧑‍💼 HR/Admin dashboard to review feedback and manage employees  
- ⚠️ Automatic high-priority alerts to HR for negative feedback  
- 🧠 Feedback history with emotion tracking  
- 🧾 CSV data export (Feedback / Directory / Summary)  
- 📦 GitHub-integrated backend data store using GitHub API  

---

## 🛠️ Tech Stack

| Category          | Technology/Library                         |
|-------------------|--------------------------------------------|
| Frontend UI       | Streamlit                                  |
| NLP Models        | HuggingFace Transformers                   |
| Sentiment Model   | distilbert-base-uncased-finetuned-sst-2-english |
| Emotion Model     | bhadresh-savani/distilbert-base-uncased-emotion |
| Data Store        | GitHub (JSON files via GitHub API)         |
| Data Analysis     | Pandas, Plotly                             |
| Authentication    | bcrypt                                     |
| Miscellaneous     | UUID, Base64, Requests, Datetime           |

---

## 🚀 Installation

1. **Clone the Repository**

```bash
git clone https://github.com/Private-Fox7/empathypulse.git
cd empathypulse
```

2. **Create a Virtual Environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. **Install Required Packages**

```bash
pip install -r requirements.txt
```

4. **Set Up GitHub Secrets**

Create a `.streamlit/secrets.toml` file:

```toml
github_token = "your_github_personal_access_token"
github_username = "your_github_username"
github_repo = "your_repo_name"
```

---

## 📦 Running the App

```bash
streamlit run empathypulse_final.py
```

Then open your browser and go to `http://localhost:8501`

---

## 📸 Screenshots

![Screenshot 2025-05-16 120713](https://github.com/user-attachments/assets/d5c1047d-8a81-47bb-b4e6-3c6b02ded965)
![Screenshot 2025-05-16 120754](https://github.com/user-attachments/assets/cc57dcb5-4220-4af8-a6c6-8849a28fcd1a)
![Screenshot 2025-05-16 120843](https://github.com/user-attachments/assets/661cff17-164d-45f6-ae68-73b7d78b8623)
![Screenshot 2025-05-16 120918](https://github.com/user-attachments/assets/02103463-79ae-42c9-a4f4-0fcf139abdca)
![Screenshot 2025-05-16 120938](https://github.com/user-attachments/assets/0ddc6503-cf16-40cf-8d81-2c79d06fa8f5)
![Screenshot 2025-05-16 120949](https://github.com/user-attachments/assets/ea6acf84-c152-4f5b-a1c5-fba172a1ed6f)
![Screenshot 2025-05-16 121002](https://github.com/user-attachments/assets/ef1fb7f7-4169-4100-adf7-c5be922fbb97)
![Screenshot 2025-05-16 121019](https://github.com/user-attachments/assets/eb0c0c15-92a2-45b3-a083-7ee53d602eb2)
![Screenshot 2025-05-16 121040](https://github.com/user-attachments/assets/665d3afe-2746-4a70-94aa-9b2a31ef807d)
---

## 🔮 Future Improvements

EmpathyPulse has a strong foundation, and here’s where we're excited to take it next:

- 💬 **Emoji-Aware Sentiment Analysis**  
  Incorporate emoji sentiment detection to better understand modern, informal feedback.

- 🔁 **Smart Learning from Feedback**  
  Enable a reinforcement learning loop where employees can correct misclassified emotions, helping the model improve over time.

- 📧 **HR Email Alerts (Real-Time)**  
  Automatically notify HR via email when serious or urgent negative feedback is detected—no need to manually check the dashboard.

- 🧠 **Custom AI Training**  
  Let organizations fine-tune sentiment models using their own historical data for even more accurate emotion recognition.

- 📊 **Advanced HR Analytics**  
  Add burnout risk scores, turnover likelihood, and trend forecasting to help HR act before problems escalate.

- 🌐 **Multilingual Feedback Support**  
  Accept and analyze employee feedback in multiple languages with real-time translation and native-language NLP models.

- 📄 **Downloadable Insights**  
  Allow HR teams to export polished PDF reports for presentations or quarterly reviews.

- 📱 **Mobile-Friendly Experience**  
  Launch a fully responsive mobile app so employees can submit feedback anytime, anywhere.

- 🔐 **Enterprise Login Integration**  
  Support Google Workspace, Microsoft Azure AD, or SSO for seamless and secure enterprise logins.

- ☁️ **Cloud Database Migration**  
  Move from GitHub-based JSON storage to scalable cloud backends (e.g., Firebase, MongoDB, Supabase) for production readiness.

- 🌈 **Real-Time Word Clouds & Heatmaps**  
  Visualize trending words and emotion clusters using live-updating word clouds and department-based heatmaps.

---

## 🧪 Deployment

You can deploy EmpathyPulse using:

- [Streamlit Cloud](https://streamlit.io/cloud)  
- [Render](https://render.com)  
- [Heroku](https://www.heroku.com/)  
- Your own server / Docker / VPS  

Be sure to set up your GitHub token and repo secrets in the deployment environment.

---

## 📄 License

MIT License – see [LICENSE](LICENSE) for full details.

---

## 📬 Contact

**Author**: [Private-Fox7]  
📧 Email: santhoshj050@gmail.com  


---

## 🙌 Contributions

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to improve.

---
