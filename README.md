# Rabbit - Economics Study Buddy

A Streamlit chatbot application that simulates Rabbit, a second-year university student studying Intermediate Microeconomics. Rabbit struggles with the subject and needs help understanding microeconomic concepts through interactive study sessions.

## Features

- **Login System**: Access code validation for secure study sessions
- **Interactive Chat**: Single-page chat interface with Rabbit
- **Study Partner Role**: Rabbit acts as a peer study partner who asks questions, makes suggestions (sometimes incorrect), and challenges explanations
- **Conversation Logging**: All study sessions are logged to MongoDB for tracking and analysis

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Secrets**:
   - Copy `.streamlit/secrets.toml` and add your MongoDB connection string and OpenAI API key
   - Set up MongoDB database with a `valid_identifiers` collection containing valid access codes

3. **Generate Access Codes**:
   ```bash
   # Generate access codes for users
   python scripts/generate_access_codes.py
   
   # Or load from existing CSV
   python scripts/load_access_codes.py
   ```

4. **Run the Application**:
   ```bash
   streamlit run rabbit_chatbot.py
   ```

## Usage

1. **Login**: Enter a valid access code to start your study session
2. **Study Session**: Chat with Rabbit to help them understand microeconomic concepts
3. **End Session**: Click "End Study Session" when finished

## Rabbit's Character

Rabbit is:
- A second-year university student studying Intermediate Microeconomics
- Struggles with the subject and is anxious about the final exam
- Friendly, informal, and chatty
- Eager to learn but often makes mistakes
- Acts as a peer study partner who asks clarifying questions and challenges explanations

## Study Session Flow

1. Rabbit shares a problem they want help solving
2. You describe what to do as a first step
3. Rabbit asks clarifying questions or questions around misconceptions
4. You answer and explain
5. Rabbit provides feedback and asks follow-up questions
6. Continue until Rabbit understands the concept

## Database Structure

The application uses MongoDB with the following collections:
- `valid_identifiers`: Contains valid access codes
- `transcripts`: Stores conversation logs with timestamps and user identifiers

## Files

- `rabbit_chatbot.py`: Main application file
- `utils/mongodb.py`: Database utilities
- `prompts/rabbit.md`: Rabbit's character prompt
- `requirements.txt`: Python dependencies
- `.streamlit/secrets.toml`: Configuration file for API keys
- `scripts/`: Access code management scripts
  - `generate_access_codes.py`: Generate new access codes
  - `load_access_codes.py`: Manage existing access codes
  - `README.md`: Script documentation
