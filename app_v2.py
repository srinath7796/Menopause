from flask import Flask, request, render_template, jsonify, redirect
from langchain.chains import ConversationalRetrievalChain
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.indexes import VectorstoreIndexCreator
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.schema import Document
import os
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv  # Import the dotenv package

app = Flask(__name__)

# Load environment variables from the .env file
load_dotenv()

# Retrieve the API key from environment variables
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


PERSIST = False

# Load or create the index
def load_text_files(directory):
    documents = []
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            with open(os.path.join(directory, filename), "r") as file:
                content = file.read()
                documents.append(Document(page_content=content, metadata={"source": filename}))
    return documents

if PERSIST and os.path.exists("persist"):
    print("Reusing index...\n")
    vectorstore = Chroma(persist_directory="persist", embedding_function=OpenAIEmbeddings())
    index = VectorStoreIndexWrapper(vectorstore=vectorstore)
else:
    documents = load_text_files("Documents/")
    embeddings = OpenAIEmbeddings()
    
    if PERSIST:
        index = VectorstoreIndexCreator(vectorstore_kwargs={"persist_directory": "persist"}, embedding=embeddings).from_documents(documents)
    else:
        index = VectorstoreIndexCreator(embedding=embeddings).from_documents(documents)

fine_tuned_model_id = "ftjob-xsqVLsiDfpP6zxLGlJhfixbP"

# Try to use the fine-tuned model, fallback to default if it fails
try:
    chain = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(model=fine_tuned_model_id),
        retriever=index.vectorstore.as_retriever(search_kwargs={"k": 1}),
    )
except Exception as e:
    print(f"Failed to load fine-tuned model: {e}. Falling back to default model.")
    chain = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(),
        retriever=index.vectorstore.as_retriever(search_kwargs={"k": 1}),
    )

chat_history = []
user_state = {}

def generate_unique_user_id():
    file_path = Path("user_data.xlsx")
    if file_path.exists():
        df = pd.read_excel(file_path)
        if not df.empty:
            last_id = df["UserID"].max()
            return last_id + 1
    return 1000

def save_to_excel(user_data):
    file_path = Path("user_data.xlsx")
    
    # Create an empty DataFrame if the file does not exist
    if not file_path.exists():
        df = pd.DataFrame(columns=["UserID", "Stage", "Data"])
    else:
        df = pd.read_excel(file_path)

    # Convert the user data to a DataFrame
    new_data = pd.DataFrame([user_data])

    # Use pd.concat() to append the new data
    df = pd.concat([df, new_data], ignore_index=True)

    # Save the updated DataFrame back to the Excel file
    df.to_excel(file_path, index=False)


def schedule_appointment(user_name, user_email):
    current_time = datetime.now()
    # Ensure the booking is within working hours (9 am to 4 pm) and avoid Sunday
    if current_time.weekday() == 6:
        current_time += timedelta(days=1)
    elif current_time.hour >= 16:
        current_time += timedelta(days=1)
    current_time = current_time.replace(hour=9, minute=0)

    appointment_time = current_time + timedelta(hours=1)
    
    # Email content
    subject = "Your Menopause Consultation is Confirmed"
    body = f"Dear {user_name},\n\nYour consultation is confirmed for {appointment_time.strftime('%Y-%m-%d %H:%M:%S')}.\n\nBest Regards,\nMenopause Assistant"
    
    send_email(user_email, subject, body)
    return appointment_time.strftime('%Y-%m-%d %H:%M:%S')

def send_email(to_email, subject, body):
    from_email = "shhhmenopause@gmail.com"
    password = "lrbiefjhqyijbmji"

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    global chat_history, user_state
    
    user_input = request.json.get("query").strip().lower()
    user_id = request.json.get("user_id")  # Track user ID for session management
    
    if not user_id:
        user_id = generate_unique_user_id()
    
    if user_input in ['quit', 'q', 'exit']:
        return jsonify({"answer": "Goodbye!"})
    
    # Initialize user state if new
    if user_id not in user_state:
        user_state[user_id] = {"stage": "greeting", "answers": {}}
    
    stage = user_state[user_id]["stage"]
    
    if stage == "greeting":
        if user_input.lower() in ["hello", "hi", "hey", "hiya", "howdy", "greetings", "helo", "helloo", 
        "hellooo", "heloo", "helooo", "hii", "hiii", "heyy", "heyyy", "hay", 
        "hayy", "hiyaa", "yo", "sup", "what's up", "whats up", "wassup", 
        "wsup", "waddup", "holla", "holaa", "yo!", "hi there", "hey there", 
        "hella"]:
            user_state[user_id]["stage"] = "menopause_assistant_offer"
            return jsonify({"answer": "Are you looking for a menopause assistant? (Yes/No)", "user_id": user_id})
    
    elif stage == "menopause_assistant_offer":
        user_state[user_id]["answers"]["looking_for_assistant"] = user_input.lower()
        if user_input.lower() == "yes":
            user_state[user_id]["stage"] = "issues_selection"
            return jsonify({"answer": "What issues are you facing from the list below? Tick all that relate to you:", 
                            "options": ["Fatigue", "Hot Flushes", "Sleep", "Mood Swings", "Restless Legs", "Vaginal Dryness", "Anxiety", 
                                       "Brain Fog", "Depression", "Dizzy Spells", "Panic Disorders", "Breast Pain", "Cramps", "Gut Health", 
                                       "Electric Shocks", "Headaches", "Joint pain", "Tension", "Brittle Nails", "Hair Thinning", "Itchy Skin", 
                                       "Tingling", "Allergies", "Burning Tongue", "Gum Issues", "Osteoporosis"]})
        else:
            user_state[user_id]["stage"] = "goodbye"
            return jsonify({"answer": "Okay! If you need help in the future, feel free to ask."})
    
    elif stage == "issues_selection":
        selected_issues = user_input.split(", ")
        user_state[user_id]["answers"]["issues"] = selected_issues
        
        user_state[user_id]["stage"] = "main_concerns"
        return jsonify({"answer": "What are your main concerns?", 
                        "options": ["Sleep", "Joint Pain", "Brain Fog", "Hot Flushes", "Intimacy"]})
    
    elif stage == "main_concerns":
        main_concerns = user_input.split(", ")
        user_state[user_id]["answers"]["main_concerns"] = main_concerns

        if "sleep" in [concern.lower() for concern in main_concerns]:  # Ensure case insensitivity
            user_state[user_id]["stage"] = "sleep_concerns"
            return jsonify({"answer": "How well do you sleep? Select one:", 
                            "options": ["Do you have trouble getting to sleep", "Do you find yourself waking up at Night", 
                                        "Do you Sleep Like a baby", "Do you get Restless Legs", "Do you get night Sweats"]})
        else:
            user_state[user_id]["stage"] = "menstrual_cycle"
            return jsonify({
                "answer": "Describe your Menstrual Cycle:",
                "options": [
                    "Regular like clock work (it is unlikely she is perimenopausal)",
                    "Not Regular For under 12 months (she is perimenopausal)",
                    "Not Regular For over 12 months (she is still perimenopausal)",
                    "Cannot Remember",
                    "Has not seen for over 12 months (postmenopausal)"
                ]
            })
    
    elif stage == "sleep_concerns":
        sleep_concerns = user_input.split(", ")
        user_state[user_id]["answers"]["sleep_concerns"] = sleep_concerns
        
        user_state[user_id]["stage"] = "menstrual_cycle"
        return jsonify({
            "answer": "Describe your Menstrual Cycle:",
            "options": [
                "Regular like clock work (it is unlikely she is perimenopausal)",
                "Not Regular For under 12 months (she is perimenopausal)",
                "Not Regular For over 12 months (she is still perimenopausal)",
                "Cannot Remember",
                "Has not seen for over 12 months (postmenopausal)"
            ]
        })

    elif stage == "menstrual_cycle":
        user_state[user_id]["answers"]["menstrual_cycle"] = user_input
        user_state[user_id]["stage"] = "age_group"
        return jsonify({"answer": "Please select your age group:", 
                        "options": ["Under 40", "40-49", "50-59", "60 and over"]})
    
    elif stage == "age_group":
        user_state[user_id]["answers"]["age_group"] = user_input
        user_state[user_id]["stage"] = "lavender_preference"
        return jsonify({"answer": "Do you like the smell of Lavender? (Yes/No/Do not Know)"})
    
    elif stage == "lavender_preference":
        lavender_preference = user_input.lower()
        user_state[user_id]["answers"]["lavender_preference"] = lavender_preference
        
        # Collect user preferences and suggest products accordingly
        sleep_concerns = user_state[user_id]["answers"].get("sleep_concerns", [])
        menstrual_cycle = user_state[user_id]["answers"].get("menstrual_cycle", "")
        
        # Adjusted logic to match exact options from menstrual cycle stage
        suggestions = []
        if lavender_preference == "yes":
            if "do you have trouble getting to sleep" in [sc.lower() for sc in sleep_concerns]:
                if "not regular for under 12 months (she is perimenopausal)" in menstrual_cycle.lower() or "not regular for over 12 months (she is still perimenopausal)" in menstrual_cycle.lower():
                    suggestions.append("Use Sleep Sound H20 if you are PeriMenopausal or Postmenopausal.")
                else:
                    suggestions.append("Use Sleep Aid if you are not peri or postmenopausal.")
            if "do you find yourself waking up at night" in [sc.lower() for sc in sleep_concerns]:
                if "not regular for under 12 months (she is perimenopausal)" in menstrual_cycle.lower() or "not regular for over 12 months (she is still perimenopausal)" in menstrual_cycle.lower():
                    suggestions.append("Use Sleep Sound H2O and Black Seed Supplement.")
                else:
                    suggestions.append("Use Sleep Aid and Black Seed.")
            if "do you sleep like a baby" in [sc.lower() for sc in sleep_concerns]:
                suggestions.append("No sleep products needed.")
            if "do you get restless legs" in [sc.lower() for sc in sleep_concerns]:
                if "not regular for under 12 months (she is perimenopausal)" in menstrual_cycle.lower() or "not regular for over 12 months (she is still perimenopausal)" in menstrual_cycle.lower():
                    suggestions.append("Use Sleep Sound H20 for Restless Legs.")
                else:
                    suggestions.append("Use Sleep Aid for Restless Legs.")
            if "do you get night sweats" in [sc.lower() for sc in sleep_concerns]:
                if "not regular for under 12 months (she is perimenopausal)" in menstrual_cycle.lower() or "not regular for over 12 months (she is still perimenopausal)" in menstrual_cycle.lower():
                    suggestions.append("Use Isoflavanes and Sleep Sound H20 for Night Sweats.")
        else:
            if "do you have trouble getting to sleep" in [sc.lower() for sc in sleep_concerns]:
                if "not regular for under 12 months (she is perimenopausal)" in menstrual_cycle.lower() or "not regular for over 12 months (she is still perimenopausal)" in menstrual_cycle.lower():
                    suggestions.append("Use Sleep Sound H20 Non Lavender if you are PeriMenopausal or Postmenopausal.")
                else:
                    suggestions.append("Use Sleep Aid Non Lavender if you are not peri or postmenopausal.")
            if "do you find yourself waking up at night" in [sc.lower() for sc in sleep_concerns]:
                if "not regular for under 12 months (she is perimenopausal)" in menstrual_cycle.lower() or "not regular for over 12 months (she is still perimenopausal)" in menstrual_cycle.lower():
                    suggestions.append("Use Sleep Sound H2O Non Lavender and Black Seed Supplement.")
                else:
                    suggestions.append("Use Sleep Aid Non Lavender and Black Seed.")
            if "do you sleep like a baby" in [sc.lower() for sc in sleep_concerns]:
                suggestions.append("No sleep products needed.")
            if "do you get restless legs" in [sc.lower() for sc in sleep_concerns]:
                if "not regular for under 12 months (she is perimenopausal)" in menstrual_cycle.lower() or "not regular for over 12 months (she is still perimenopausal)" in menstrual_cycle.lower():
                    suggestions.append("Use Sleep Sound H20 Non Lavender for Restless Legs.")
                else:
                    suggestions.append("Use Sleep Aid Non Lavender for Restless Legs.")
            if "do you get night sweats" in [sc.lower() for sc in sleep_concerns]:
                if "not regular for under 12 months (she is perimenopausal)" in menstrual_cycle.lower() or "not regular for over 12 months (she is still perimenopausal)" in menstrual_cycle.lower():
                    suggestions.append("Use Isoflavanes and Sleep Sound H20 Non Lavender for Night Sweats.")

        suggestion_text = "Based on your preferences, here are some suggestions: " + "; ".join(suggestions) + "."
        
        user_state[user_id]["answers"]["product_suggestions"] = suggestions
        
        # Move to consultation offer stage after product suggestions
        user_state[user_id]["stage"] = "consultation_offer"
        return jsonify({
            "answer": suggestion_text,
            "follow_up": "Would you like to book a Menopause Consultation? (Yes/No)"
        })
    
    elif stage == "consultation_offer":
        user_state[user_id]["answers"]["consultation_offer"] = user_input.lower()
        if user_input.lower() == "yes":
            save_to_excel({
                "UserID": user_id,
                "Stage": "completed",
                "Data": user_state[user_id]["answers"]
            })
            return jsonify({"redirect": "/consultation"})
        else:
            return jsonify({"answer": "Okay! If you need further assistance, feel free to ask."})

    return jsonify({"answer": "I'm sorry, I didn't understand that. Can you please rephrase?"})

@app.route("/consultation", methods=["GET", "POST"])
def consultation():
    if request.method == "POST":
        user_id = request.form["user_id"]
        name = request.form["name"]
        email = request.form["email"]

        # Schedule the appointment
        appointment_time = schedule_appointment(name, email)

        # Save the data in Excel
        user_data = {
            "UserID": user_id,
            "Stage": "consultation",
            "Data": f"Name: {name}, Email: {email}, Appointment Time: {appointment_time}"
        }
        save_to_excel(user_data)

        return jsonify({"message": "Your consultation is confirmed!", "appointment_time": appointment_time})
    
    return render_template("consultation.html")

if __name__ == "__main__":
    app.run(debug=True)
