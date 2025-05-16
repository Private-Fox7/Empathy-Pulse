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
| Frontend UI       | [Streamlit](https://streamlit.io)          |
| NLP Models        | [HuggingFace Transformers](https://huggingface.co/) |
| Sentiment Model   | `distilbert-base-uncased-finetuned-sst-2-english` |
| Emotion Model     | `bhadresh-savani/distilbert-base-uncased-emotion` |
| Data Store        | GitHub (JSON files using GitHub API)       |
| Data Analysis     | Pandas, Plotly                             |
| Authentication    | bcrypt                                     |
| Misc              | UUID, Base64, Requests, Datetime           |

---

## 🚀 Installation

1. **Clone the Repository**

```bash
git clone https://github.com/yourusername/empathypulse.git
cd empathypulse

**Running the Application**
  Command : streamlit run empathypulse_final.py


**Contact**
Author : Private-Fox7
email : santhoshj050@gmail.com


**🙌 Contributions**
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.
