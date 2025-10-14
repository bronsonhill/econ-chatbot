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
    economics_problem = """Assume that a perfectly competitive, constant-cost industry (with free entry and exit) is in along-run equilibrium with 40 firms. The market demand function is downward sloping. All firms have the same U-shaped average cost functions. Each firm produces 60 units of output, which it sells at a price of $27 per unit; out of this amount, each firm pays a $3 tax per unit of output. Please refer to the graphs below, which depict the initial equilibrium.

The government decides to decrease the tax so that firms will pay \$1 per unit in tax.

a) Consider the graphs below, which depict the initial long-run (LR) equilibrium. What are the equilibrium price pA and output QA? What is the output qa? What is the profit ofeach firm? Why? How could we determine from the graphs that this industry is indeed in the LR equilibrium?

b) Explain what would happen in the short run (SR) to the equilibrium price and industry output, the number of firms in the industry, output and profit of each firm. Illustrate on graphs for the market and a particular firm. Please label the market equilibrium point as B (price pB and output QB) and the firm’s point as b (output qb).

c) Explain what would happen in the long run (LR) to the equilibrium price and industry output, the number of firms in the industry, and the output and profit of each firm. Illustrate on graphs for the market and a particular firm. Please label the market equilibrium point as C (price pC and output QC) and the firm’s point as c (output qc). Compare this new long-run equilibrium to the initial long-run equilibrium, described in part (a), and to the short-run equilibrium found in part (b).
"""

    economics_solution = """a) The initial long-run (LR) equilibrium. The initial market equilibrium is at point A, where market demand intersects the initial SR industry supply (which is upward sloping). At the same point, the demand intersects the LR industry supply (which is a horizontal line at the price pA). We know that the current LR equilibrium price is pA = \$27. This is the price consumers pay. Firms receive this price and then pay \$3 in tax to the government. Because there are 40 firms in the industry, and each firm produces output $qa = 60$ units, the market (industry) output is $QA = 40*60 = 2400$. The average cost curve (AC) of each firm takes into account the \$3 per unit tax. Each firm produces at the minimum of its AC, which is achieved at the output $qa= 60$. This is represented by point a on the graph for the firm below (on the right). To maximise its profit, each firm produces the output such that price equals MC. Here, the price also equals the minimum of the average cost AC. When price equals AC, a firm's profit is zero. Because firms make zero profits in equilibrium, we know that this industry is in the LR equilibrium.

b) per unit tax decreased by $2, Short-Run (SR) equilibrium. 
    
After tax is reduced by \$2, the average cost (AC) and the marginal cost (MC) curves of each firm shift down by the amount of tax decrease, $Δt = \$2$ (because this is a per-unit tax, the reduction in AC and MC is equal to the reduction in tax, \$2). Therefore, the minimum of the new AC will be at \$25. The number of firms in the industry stays the same in SR because firms are not able to enter or exit the industry in SR. Therefore, the industry supply, which is the horizontal sum of the supplies of all firms, shifts down by $2 as well. We can also think of it as a shift of SR industry supply to the right.

What would happen in the SR equilibrium? The demand function stays the same, but the supply function shifts down (or to the right); therefore, the new intersection point B, the new SR equilibrium, will correspond to a lower price pB and the higher output QB.

Because the demand function is downward sloping, and the downward-sloping supply function shifts down by \$2, the price will decrease by less than \$2.

SR equilibrium (summary): price is pB (decreases from the initial price of \$27 by less than \$2), market output is QB, higher than the initial quantity of 2400. The market SR equilibrium is at point B. The number of firms stays the same.

At the new SR equilibrium price, pB, each firm produces output qb. At this output, the MC of the firm equals the price, which guarantees that the firm maximises its profit. The output qb is greater than $qa = 60$, because MC and AC shifts down by \$2, but the price decreases by less than \$2. The output qb is not at the minimum of the AC for tax = \$1, it is to the right. Therefore, at this output, MC (which is equal to price pb) is above the AC, and the firm will make a positive profit (represented by the green rectangle). 

Each firm in the SR equilibrium (summary): output is $qb > qa = 60$; profit is positive.

c) per unit tax decreased by \$2, Long Run (LR) equilibrium.

What would happen in the long run? Because each firm makes a positive profit in SR, this could not be an LR equilibrium. Attracted by positive profits, new firms start entering the industry. As a result, the SR industry supply shifts even further to the right (because more firms can produce more output for any given price). As more firms keep entering, the industry supply shifts further and further. 

As demand stays the same (does not shift), but supply increases (shifts to the right), the market price decreases. How long will this process of firms entering and price decreasing continue? The firms will enter as long as profits are positive. Because more firms result in a lower market price for their output, the profits in the industry decrease as the number of firms increases. Note that each firm will also decrease its output in response to a lower price. Firms will enter until the price reaches $pC = \$25$, the new minimum of the ACLR curve, when firms make zero profit.

Therefore, in the LR, the price will decrease by exactly the amount of tax reduction, \$2.

New LR equilibrium (summary): price $pC = \$25$, output QC (LR equilibrium is at point C); more firms in the industry; each firm produces output $qa= 60$ and makes zero profit.

Compared to the initial LR equilibrium (described in part a): price down to \$25 (it decreases by the same amount as the tax decrease, \$2), market output Q is up, quantity produced by each firm is the same: $qa  = 60$, profits are the same (equal to zero), the number of firms N increased.

Compared to the SR equilibrium (found in part b): price is down, market output is up, quantity produced by each firm is down, profits are down to 0, and the number of firms in the industry, N, increased.

    
    """

    return base_prompt + "\n\n## The Economics Problem\n" + economics_problem + "\n\n## The Solution\n" + economics_solution

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
            "rabbit_v3": "V3 - Hints",
            "rabbit_v4": "V4 - Focussed role with misconceptions",
            "rabbit_v5": "V5 - Problem and Solution v5 with example transcript"
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
    st.markdown("""Assume that a perfectly competitive, constant-cost industry (with free entry and exit) is in along-run equilibrium with 40 firms. The market demand function is downward sloping. All firms have the same U-shaped average cost functions. Each firm produces 60 units of output, which it sells at a price of $27 per unit; out of this amount, each firm pays a $3 tax per unit of output. Please refer to the graphs below, which depict the initial equilibrium.

The government decides to decrease the tax so that firms will pay \$1 per unit in tax.

a) Consider the graphs below, which depict the initial long-run (LR) equilibrium. What are the equilibrium price pA and output QA? What is the output qa? What is the profit ofeach firm? Why? How could we determine from the graphs that this industry is indeed in the LR equilibrium?

b) Explain what would happen in the short run (SR) to the equilibrium price and industry output, the number of firms in the industry, output and profit of each firm. Illustrate on graphs for the market and a particular firm. Please label the market equilibrium point as B (price pB and output QB) and the firm’s point as b (output qb).

c) Explain what would happen in the long run (LR) to the equilibrium price and industry output, the number of firms in the industry, and the output and profit of each firm. Illustrate on graphs for the market and a particular firm. Please label the market equilibrium point as C (price pC and output QC) and the firm’s point as c (output qc). Compare this new long-run equilibrium to the initial long-run equilibrium, described in part (a), and to the short-run equilibrium found in part (b).
""")
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
                        max_output_tokens=250,
                        reasoning={"effort": "minimal"}
                    )

                    # Handle streaming response
                    response_container = st.empty()
                    response_text = ""

                    for chunk in stream:
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
                        max_tokens=250
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
                        max_tokens=250
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
