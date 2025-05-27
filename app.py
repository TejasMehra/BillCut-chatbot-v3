import streamlit as st
import google.generativeai as genai
import os

# --- API Key Loader ---
def get_api_key():
    try:
        return st.secrets["GOOGLE_API_KEY"]
    except KeyError:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("Please set the GOOGLE_API_KEY in Streamlit secrets or environment.")
            return None
        return api_key

# --- Gemini Setup ---
api_key = get_api_key()
if api_key:
    genai.configure(api_key=api_key)
else:
    st.stop()

# --- System Prompt ---
system_prompt = """
You are Sophie, a helpful and friendly AI assistant for BillCut — a company that helps people in India get out of debt.

Your tone is:
- Friendly but very respectful. Always talk like you are talking to a senior no matter the language.
- Fun and a bit quirky
- Supportive and to-the-point

Your job:
- Explain how BillCut helps with loans, EMIs, debt settlement, and money habits.
- Use short, clear sentences.
- Bring the conversation back to BillCut when possible.
- Let the user lead — end the conversation naturally without forcing lines like “Want me to explain in detail?”.
- If the user uses even a little Hindi or Hinglish — or mixes English and Hindi — always reply in Hinglish. 
- Never default to English if Hindi or Hinglish is present in any form. Prefer Hinglish over Hindi if the user types in Latin script.


Never start replies with “Hi” or “Hey”.
"""

# --- Scripted Responses ---
faq_responses = {
    "what is billcut": "BillCut is a fintech company that does debt refinancing. Want to know more?",
    "does billcut charge": "BillCut doesn’t charge any fees, except ₹19 for a session with our legal advisor during debt settlement.",
    "interest rate": "The interest rate is usually between 12 to 19 percent.",
    "multiple loans": "Yes! You can combine multiple  loans into a single loan  .",
    "how does billcut pay": "BillCut works with NBFCs. They provide the loan for your existing loans ",
    "will the funds come": "Yes! Funds come to your account — except in balance transfers, which may use a demand draft.",
    "foreclosure charge": "It's around 3% of the remaining amount.",
    "credit score": "Nope! Your score won’t be affected — unless you go for debt settlement.",
    "why work email": "Just to verify your job in the company , we wont be sending any mails on it ",
    "what is demand draft": "It's like a prepaid cheque — but safer, and it can’t bounce.",
    "what are nbfc": "NBFCs give loans like banks — but they’re not banks.",
    "full form of nbfc": "NBFC stands for Non-Banking Financial Company.",
    "how does billcut pay credit card": "BillCut pays your card via its lending partners.",
    "what is debt settlement": "Debt settlement means reducing your outstanding loan or credit card dues — up to 50% — if you're under financial stress or facing recovery calls. It’s not a loan."
}

detailed_followups = {
    "what is billcut": "Sure! BillCut is a financial platform that helps you manage and reduce your existing debt. We partner with NBFCs (Non-Banking Financial Companies) to refinance your high-interest credit card bills and personal loans into affordable EMIs. This makes your repayments easier and more predictable. We also offer a debt settlement service for people going through tough financial situations. Would you like me to explain how settlement works too?",  
    "how does billcut pay credit card": "Absolutely. BillCut, through its lending partners, helps you pay off your credit card bill in full. Here’s how it works: the NBFC transfers funds to your bank account — once you receive the money, you pay your credit card bill and show us the proof. Meanwhile, the amount is converted into a single, low-interest EMI which you repay gradually. This process is simple, transparent, and designed to ease your monthly financial load.",
    "what is debt settlement": "Debt settlement is a special service we offer if you're under serious financial stress or facing recovery calls. In this case, BillCut negotiates with your bank or credit card issuer to reduce the total amount you owe — up to 50%. Instead of taking a loan, you settle your dues with a one-time payment or structured plan. Please note, while this does impact your credit score, it's a great option if you're struggling to repay the full amount. Want help checking your eligibility?"
}

repeat_followups = {
    "what is billcut": "Just to recap — BillCut is here to make your debt more manageable. We convert your high-interest loans into structured EMIs and even help negotiate reductions in extreme cases. If you’re unsure about what’s right for your situation, I’d be happy to guide you through it!",
    "how does billcut pay credit card": "As a quick reminder — we don’t pay the card directly. Our lending partner sends money to your bank account, you pay your card bill with it, and then you repay that amount to the NBFC in EMIs. Would you like to get started with your application?",
    "what is debt settlement": "In case you missed it — debt settlement is a way to reduce your total dues if you're unable to repay. It’s not a loan. We negotiate with lenders for you, and if you qualify, it can bring significant relief. Want us to check if you’re eligible?"
}




# --- Streamlit App UI ---
st.title("👋 Hi, how can I help you?")
st.caption("Type full questions in Hindi, Hinglish, or English — I will match your style!")

# --- Session State ---
if "chat" not in st.session_state:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-8b",
        system_instruction=system_prompt
    )
    st.session_state.chat = model.start_chat(history=[])

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_question_key" not in st.session_state:
    st.session_state.last_question_key = None

if "followup_count" not in st.session_state:
    st.session_state.followup_count = 0

# --- Display Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Chat Input Logic ---
if user_input := st.chat_input("Ask me anything about BillCut..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    input_lower = user_input.lower().strip()
    response = None

    if input_lower in ["yes", "yeah", "sure", "ok", "okay"]:
        key = st.session_state.last_question_key
        count = st.session_state.followup_count

        if key:
            if count == 0 and key in detailed_followups:
                response = detailed_followups[key]
                st.session_state.followup_count += 1
            elif count == 1 and key in repeat_followups:
                response = repeat_followups[key]
                st.session_state.followup_count += 1
            else:
                try:
                    # First message soft language nudge
                    if len(st.session_state.messages) <= 1:
                        user_input += "\n\n(Please reply in the same language I used above)"
                    response = st.session_state.chat.send_message(user_input).text
                except Exception as e:
                    response = "Oops! Something went wrong. Try again?"
                    print("Gemini error:", e)
        else:
            try:
                response = st.session_state.chat.send_message(user_input).text
            except Exception as e:
                response = "Oops! Something went wrong. Try again?"
                print("Gemini error:", e)

    else:
        match = None
        for key in faq_responses:
            if key in input_lower:
                match = key
                break

        if match:
            response = faq_responses[match]
            st.session_state.last_question_key = match
            st.session_state.followup_count = 0
        else:
            try:
                response = st.session_state.chat.send_message(user_input).text
            except Exception as e:
                response = "Oops! Something went wrong. Try again?"
                print("Gemini error:", e)
            st.session_state.last_question_key = None
            st.session_state.followup_count = 0

    # Display response
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)
