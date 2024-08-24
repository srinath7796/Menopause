# Menopause Chatbot

This repository contains a Flask-based AI-driven chatbot designed to assist women during menopause. The chatbot leverages OpenAI's GPT models and LangChain for conversational retrieval, providing personalized advice based on user symptoms. Additionally, the chatbot can schedule consultations, send confirmation emails, and save user data.

## Features

- **AI-Powered Chatbot**: Provides personalized recommendations for menopause-related issues such as sleep problems, hot flashes, anxiety, and more using OpenAI GPT models.
- **Conversational Retrieval Chain**: Uses LangChain and Chroma vectorstore to retrieve contextually relevant information from a pre-built index of documents.
- **Consultation Scheduling**: Users can schedule menopause consultations, and the chatbot sends a confirmation email with appointment details.
- **User Data Management**: Saves user data, such as symptoms and preferences, to an Excel file for future analysis.
- **Customizable Workflow**: The chatbot is designed to be flexible and customizable based on specific user interactions and recommendations.

## Prerequisites

Make sure you have the following installed:

- Python 3.x
- Flask
- OpenAI API
- pandas
- dotenv (for managing environment variables)

## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/srinath7796/Menopause.git
   cd Menopause


pip install -r requirements.txt

OPENAI_API_KEY=your_openai_api_key
EMAIL_USER=your_email@example.com
EMAIL_PASSWORD=your_email_password

flask run

├── app.py                  # Main Flask application file
├── .env                    # Environment variables for API keys and email credentials
├── requirements.txt        # Required Python packages
├── Documents/              # Folder containing text files for document indexing
├── templates/              # HTML templates for the frontend
│   ├── index.html
│   └── consultation.html
├── static/                 # Static files (CSS, JS)
└── user_data.xlsx          # Stores user interaction data



Usage
Chat with the Bot: Users can interact with the chatbot through the web interface (index.html). The chatbot asks questions to assess the user's symptoms and preferences.
Receive Suggestions: Based on the user's responses, the chatbot suggests products or solutions for managing menopause-related issues.
Book Consultations: Users can book a menopause consultation, and a confirmation email with appointment details is sent.
Data Storage: User interactions are stored in an Excel file (user_data.xlsx) for future analysis.
Email Notification
The chatbot sends email notifications using Gmail's SMTP server. Ensure that "less secure app access" is enabled in your Gmail account or use an app-specific password.

License
This project is licensed under the MIT License.

Contributions
Contributions are welcome! Feel free to open issues or submit pull requests for improvements or bug fixes.

Acknowledgments
OpenAI for GPT models.
LangChain for conversational retrieval.
Flask for the web framework.
