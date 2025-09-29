from openai.types.shared.reasoning_effort import ReasoningEffort
from pandas import read_sas
import streamlit as st
from openai import OpenAI
from utils.mongodb import check_identifier
import os

def is_identifier_valid():
    identifier = st.session_state.get("user_identifier", "").strip()
    if not identifier:
        return False
    return check_identifier(st.session_state["mongodb_uri"], identifier)

def load_available_prompts():
    """Load all available prompt variations from the prompts directory"""
    prompts_dir = "./prompts"
    prompts = {}

    if os.path.exists(prompts_dir):
        for filename in os.listdir(prompts_dir):
            if filename.startswith('rabbit_v') and filename.endswith('.md'):
                prompt_name = filename[:-3]  # Remove .md extension
                with open(os.path.join(prompts_dir, filename), 'r') as file:
                    prompt_content = file.read()
                    prompts[prompt_name] = prompt_content

    return prompts

def get_prompt_with_context(prompt_name):
    """Get a prompt with the economics problem context"""
    base_prompt = load_available_prompts().get(prompt_name, "")

    # Add the same economics problem context for all prompt variations
    economics_context = """Assume that a perfectly competitive, constant-cost industry is in a long-run equilibrium with 40 firms. The market demand function is downward sloping. All firms have the same U-shaped average cost functions. Each firm produces 60 units of output, which it sells at a price of \$27 per unit; out of this amount, each firm pays a \$3 tax per unit of output. Please refer to the graph below, which depicts the initial equilibrium.

The government decides to decrease the tax so that firms will pay \$1 per unit in tax.

a) Explain what would happen in the short run to the equilibrium price and industry output, the number of firms in the industry, output and profit of each firm. Illustrate on graphs for the market and a particular firm.

b) Explain what would happen in the long run to the equilibrium price and industry output, the number of firms in the industry, and the output and profit of each firm. Illustrate on graphs for the market and a particular firm. Compare this new long-run equilibrium to the initial long-run equilibrium and to the short-run equilibrium found in a)."""

    return base_prompt + "\n\n## The Economics Problem\n" + economics_context

def setup():
    # Load available prompt variations
    available_prompts = load_available_prompts()

    # Initialize current prompt if not set
    if "current_prompt" not in st.session_state:
        st.session_state["current_prompt"] = "rabbit_v1"  # Default to first variation

    # Load current prompt with context
    current_prompt_name = st.session_state["current_prompt"]
    if "current_prompt_content" not in st.session_state or st.session_state.get("prompt_version") != current_prompt_name:
        st.session_state["current_prompt_content"] = get_prompt_with_context(current_prompt_name)
        st.session_state["prompt_version"] = current_prompt_name

    # Set up model
    if "model" not in st.session_state:
        st.session_state["model"] = "gpt-5"

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Initialize response counter
    if "response_counter" not in st.session_state:
        st.session_state["response_counter"] = 0

    # Initialize conversation state
    if "conversation_finished" not in st.session_state:
        st.session_state["conversation_finished"] = False

    # MongoDB connection
    if "mongodb_uri" not in st.session_state:
        st.session_state["mongodb_uri"] = st.secrets["MONGODB_CONNECTION_STRING"]

    # Session tracking
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = None

    # User identifier
    if "user_identifier" not in st.session_state:
        st.session_state["user_identifier"] = ""

    # Hint system
    if "hint_index" not in st.session_state:
        st.session_state["hint_index"] = 0

    # Track recent hints for conversation context
    if "recent_hints" not in st.session_state:
        st.session_state["recent_hints"] = []

    # OpenAI conversation ID
    if "openai_conversation_id" not in st.session_state:
        st.session_state["openai_conversation_id"] = None

    # Set up OpenAI API client
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    return client

def create_or_get_conversation(client):
    """Create a new conversation thread or retrieve existing one"""
    if not st.session_state.get("openai_conversation_id"):
        try:
            # Create new conversation
            conversation = client.conversations.create(
                items=[
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": "Hi, I am Rabbit! What is your name?"
                    }
                ],
                metadata={
                    "user_identifier": st.session_state.get("user_identifier", "unknown"),
                    "session_type": "economics_study"
                }
            )
            st.session_state["openai_conversation_id"] = conversation.id
        except Exception as e:
            st.error(f"Error creating conversation: {e}")
            return None
    return st.session_state["openai_conversation_id"]

def get_conversation_info(client, conversation_id):
    """Retrieve conversation information"""
    try:
        conversation = client.conversations.retrieve(conversation_id)
        return conversation
    except Exception as e:
        st.warning(f"Could not retrieve conversation info: {e}")
        return None

def clear_conversation():
    """Clear the current conversation"""
    st.session_state["openai_conversation_id"] = None
    st.session_state["chat_history"] = []
    st.session_state["response_counter"] = 0
    st.session_state["conversation_finished"] = False
    st.session_state["hint_index"] = 0  # Reset hint index when clearing conversation
    st.session_state["recent_hints"] = []  # Clear recent hints when clearing conversation

def get_next_hint():
    """Get the next hint from solution.md"""
    try:
        with open("prompts/solution.md", 'r') as file:
            lines = file.readlines()
            current_index = st.session_state.get("hint_index", 0)

            # Keep looking for the next non-empty line
            while current_index < len(lines):
                hint_line = lines[current_index].strip()
                if hint_line:  # Found a non-empty line
                    return hint_line, current_index
                current_index += 1

            return None, -1  # No more hints available
    except FileNotFoundError:
        return None, -1

def show_next_hint():
    """Add the next hint to chat history"""
    hint, hint_line_index = get_next_hint()
    if hint is not None:
        hint_message = f"Let's read a hint: {hint}"
        st.session_state.chat_history.append({"role": "assistant", "content": hint_message})
        # Add hint to recent hints for conversation context
        st.session_state.recent_hints.append(hint_message)
        # Update hint_index to point to the next line to check
        st.session_state.hint_index = hint_line_index + 1
        st.rerun()

def change_prompt_and_reset(new_prompt):
    """Change the current prompt and reset conversation"""
    if st.session_state.get("current_prompt") != new_prompt:
        st.session_state["current_prompt"] = new_prompt
        st.session_state["current_prompt_content"] = get_prompt_with_context(new_prompt)
        st.session_state["prompt_version"] = new_prompt
        clear_conversation()
        st.rerun()

def login_page():
    setup()
    st.title("🐰 Rabbit - Economics Study Buddy")
    st.markdown(
        "Welcome! You'll be helping Rabbit, a second-year university student who studies Intermediate Microeconomics. "
        "Rabbit struggles with the subject and is anxious about the final exam. "
        "You'll work together as study partners to practice microeconomic problems."
    )
    
    st.markdown(
        "## Instructions\n"
        "1. Enter your unique access code below to start your study session with Rabbit.\n"
        "2. Once logged in, you'll chat with Rabbit and help them understand microeconomic concepts.\n"
        "3. Rabbit will ask questions, make suggestions (sometimes incorrect), and challenge your explanations.\n"
        "4. Work through problems step-by-step together until Rabbit understands the concepts.\n"
        "\n**Note:** Please ensure you have a stable internet connection."
    )

    # Add identifier input
    identifier = st.text_input(
        "Please enter your access code:",
        key="identifier_input",
        value=st.session_state.get("user_identifier", ""),
        help="This access code will be used to track your study session"
    )

    if identifier:
        if check_identifier(st.session_state["mongodb_uri"], identifier):
            st.session_state["user_identifier"] = identifier
            st.success("✅ Access code validated successfully! You can now start your study session with Rabbit.")
            if st.button("Start Study Session", type="primary"):
                # Clear any existing conversation for new user
                clear_conversation()
                st.session_state["show_chat"] = True
                st.rerun()
        else:
            st.error("❌ Invalid access code. Please enter a valid access code.")
            st.session_state["user_identifier"] = ""
    else:
        st.warning("⚠️ Please enter your access code before starting the study session.")

def chat_page():
    client = setup()

    st.title("🐰 Study Session with Rabbit")

    # Sidebar with prompt selection and conversation management
    with st.sidebar:
        st.markdown("## 🧪 Prompt Testing")

        # Get available prompts
        available_prompts = load_available_prompts()
        prompt_names = list(available_prompts.keys())

        # Create display names for prompt variations
        prompt_display_names = {
            "rabbit_v1": "V1 - Not given solution ",
            "rabbit_v2": "V2 - Given solution",
            "rabbit_v3": "V3 - Hints"
        }

        # Current prompt selection
        current_prompt = st.session_state.get("current_prompt", "rabbit_v1")
        display_options = [prompt_display_names.get(name, name) for name in prompt_names]

        selected_display = st.selectbox(
            "Choose prompt variation for testing:",
            options=display_options,
            index=prompt_names.index(current_prompt) if current_prompt in prompt_names else 0,
            key="prompt_selector"
        )

        # Map back to prompt name
        selected_prompt_name = prompt_names[display_options.index(selected_display)]

        # Handle prompt change
        if selected_prompt_name != current_prompt:
            change_prompt_and_reset(selected_prompt_name)

        st.markdown("---")

        # Conversation management
        conversation_id = st.session_state.get("openai_conversation_id")
        if conversation_id:
            if st.button("🔄 New Conversation", help="Start a fresh conversation"):
                clear_conversation()
                st.rerun()
        else:
            st.info("No active conversation")

        st.markdown("---")
        st.markdown(f"**Current Prompt:** {prompt_display_names.get(current_prompt, current_prompt)}")
    st.markdown("*Help Rabbit understand Intermediate Microeconomics concepts*")
    st.markdown("### Problem: Tax in a Perfectly Competitive Industry")
    st.markdown("Assume that a perfectly competitive, constant-cost industry is in a long-run equilibrium with 40 firms. The market demand function is downward sloping. All firms have the same U-shaped average cost functions. Each firm produces 60 units of output, which it sells at a price of \$27 per unit; out of this amount, each firm pays a \$3 tax per unit of output. Please refer to the graph below, which depicts the initial equilibrium.")
    st.markdown("The government decides to decrease the tax so that firms will pay \$1 per unit in tax.")
    st.markdown("a) Explain what would happen in the short run to the equilibrium price and industry output, the number of firms in the industry, output and profit of each firm. Illustrate on graphs for the market and a particular firm.")
    st.markdown("b) Explain what would happen in the long run to the equilibrium price and industry output, the number of firms in the industry, and the output and profit of each firm. Illustrate on graphs for the market and a particular firm. Compare this new long-run equilibrium to the initial long-run equilibrium and to the short-run equilibrium found in a).")
    st.image("prompts/tax_in_a_perfectly_competitive_industry.png", output_format="auto", channels="RGB", caption=None)
    st.markdown(
        """
        <style>
        img {
            background-color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    # Add initial Rabbit message if chat history is empty
    if not st.session_state.chat_history:
        initial_message = "Hi, I am Rabbit! What is your name?"
        st.session_state.chat_history.append({"role": "assistant", "content": initial_message})

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    MAXIMUM_RESPONSES = 1000
    
    if prompt := st.chat_input(
        "Type your message to Rabbit here...",
        disabled=st.session_state.conversation_finished or st.session_state.response_counter >= MAXIMUM_RESPONSES
    ):
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate Rabbit's response
        if st.session_state.response_counter < MAXIMUM_RESPONSES:
            with st.chat_message("assistant"):
                # Get or create conversation ID
                conversation_id = create_or_get_conversation(client)
                if not conversation_id:
                    st.error("Failed to create conversation. Please try again.")
                    return

                # Get streaming response from OpenAI using Responses API
                response = ""  # Initialize response variable

                # Combine recent hints with current user input
                recent_hints_text = "\n".join(st.session_state.recent_hints) if st.session_state.recent_hints else ""
                combined_input = f"{recent_hints_text}\n\nUser: {prompt}".strip()

                try:
                    stream = client.responses.create(
                        model=st.session_state["model"],
                        conversation=conversation_id,  # Use conversation ID, not messages array
                        input=combined_input,  # Pass combined input with recent hints
                        instructions=st.session_state["current_prompt_content"],
                        stream=True,
                        max_output_tokens=500,
                        reasoning={"effort": "minimal"}
                    )

                    # Handle streaming response
                    response_container = st.empty()
                    response_text = ""

                    for chunk in stream:
                        print(chunk)
                        # Handle different chunk types from OpenAI Responses API
                        if hasattr(chunk, 'type'):
                            chunk_type = chunk.type

                            # Handle text delta events
                            if chunk_type == 'response.output_text.delta':
                                if hasattr(chunk, 'delta') and chunk.delta:
                                    response_text += chunk.delta
                                    response_container.markdown(response_text)
                        else:
                            # Fallback for any other format
                            if hasattr(chunk, 'content') and chunk.content:
                                response_text += chunk.content
                                response_container.markdown(response_text)

                    response = response_text

                except Exception as e:
                    st.error(f"Error generating response: {e}")
                    response = ""  # Ensure response is set even on error
                    # Fallback to chat completions API
                    messages = [
                        {"role": "system", "content": st.session_state["current_prompt_content"]}
                    ] + [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.chat_history
                    ]

                    fallback_stream = client.chat.completions.create(
                        model=st.session_state["model"],
                        messages=messages,
                        stream=True,
                        max_tokens=500
                    )

                    response_container = st.empty()
                    response_text = ""
                    for chunk in fallback_stream:
                        if chunk.choices[0].delta.content is not None:
                            response_text += chunk.choices[0].delta.content
                            response_container.markdown(response_text)

                    response = response_text

                except Exception as e:
                    st.error(f"Error generating response: {e}")
                    response = ""  # Ensure response is set even on error
                    # Fallback to chat completions API
                    messages = [
                        {"role": "system", "content": st.session_state["current_prompt_content"]}
                    ] + [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.chat_history
                    ]

                    fallback_stream = client.chat.completions.create(
                        model=st.session_state["model"],
                        messages=messages,
                        stream=True,
                        max_tokens=500
                    )

                    response_container = st.empty()
                    response_text = ""
                    for chunk in fallback_stream:
                        if chunk.choices[0].delta.content is not None:
                            response_text += chunk.choices[0].delta.content
                            response_container.markdown(response_text)

                    response = response_text

            # Update counters and history
            st.session_state.response_counter += 1
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            # Clear recent hints after each response to prevent accumulation
            st.session_state.recent_hints = []
        else:
            # Maximum responses reached
            with st.chat_message("assistant"):
                st.markdown("Thanks for helping me study! I think I understand this topic much better now. 🐰")
            
            final_message = {"role": "assistant", "content": "Thanks for helping me study! I think I understand this topic much better now. 🐰"}
            st.session_state.chat_history.append(final_message)
            st.session_state.conversation_finished = True

    # Action buttons
    col1, col2, col3, col4 = st.columns([1, 1.5, 1.5, 1])

    # Show Hint button
    with col2:
        hint_available, _ = get_next_hint()
        current_prompt = st.session_state.get("current_prompt", "rabbit_v1")
        if (not st.session_state.conversation_finished and
            st.session_state.chat_history and
            hint_available and
            current_prompt == "rabbit_v3"):
            if st.button("Show Hint", key="show_hint", use_container_width=True):
                show_next_hint()

    # End Study Session button
    with col3:
        if not st.session_state.conversation_finished and st.session_state.chat_history:
            if st.button("End Study Session", key="finish_chat", use_container_width=True, type="primary"):
                st.session_state.conversation_finished = True
                # Log the conversation
                from utils.mongodb import log_transcript
                session_id = log_transcript(
                    st.session_state["mongodb_uri"],
                    "rabbit_study",
                    st.session_state.chat_history
                )
                st.session_state.session_id = session_id
                st.success("Study session completed! Your conversation has been saved.")
                st.rerun()

def main():
    # Check if user is logged in and should see chat
    if st.session_state.get("show_chat", False) and is_identifier_valid():
        chat_page()
    else:
        login_page()

if __name__ == "__main__":
    main()
