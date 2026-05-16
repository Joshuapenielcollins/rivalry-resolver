# ⚔️ Rivalry Resolver

**Rivalry Resolver** is an agentic AI platform designed to gamify friend-vs-friend cricket rivalries. It uses Gemini 1.5 Flash to act as an impartial (but spicy) referee, adjudicating disputes and generating real-time match predictions.

## ✨ Features
- **🤖 AI Referee**: Real-time adjudication of arguments and disputes.
- **🎯 Interactive Predictions**: Users can make their own calls on match scenarios.
- **🚀 Auto-Play Match Engine**: Simulates live match events with configurable speeds.
- **💎 Premium UI**: Modern glassmorphic dark-theme interface.
- **🏆 Tier System**: Level up from "Casual Banter" to "Hall of Flame".
- **💀 Forfeit Enforcement**: Loser's forfeit is tracked and highlighted at the end.

- Live Url : https://rivalry-resolver-766923802801.asia-south1.run.app/

## 🛠️ Tech Stack
- **Frontend**: [Streamlit](https://streamlit.io/)
- **AI Core**: [Google Gemini 1.5 Flash](https://aistudio.google.com/)
- **Deployment**: [Google Cloud Run](https://cloud.google.com/run)

## 🚀 Local Setup
1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd rivalry-resolver
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your Gemini API Key:
   ```bash
   export GOOGLE_API_KEY="your-api-key"
   ```
4. Run the app:
   ```bash
   streamlit run app.py
   ```

## ☁️ Deployment
This app is ready to be deployed to Google Cloud Run using the provided `Dockerfile`.
```bash
gcloud run deploy rivalry-resolver --source .
```

---
Built with ❤️ for cricket fans.
