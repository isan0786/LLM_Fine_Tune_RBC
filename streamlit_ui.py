import openai
import streamlit as st
from streamlit_chat import message
from dotenv import load_dotenv
import os
import json
from serpapi import GoogleSearch

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
fine_tuned_model_id = 'ft:gpt-3.5-turbo-0125:personal:di-txn-assist:9GCDhNRR'
# Set org ID and API key
openai.api_key = os.getenv("API_KEY")
openai.base_url = os.getenv("BASE_URL")
serp_api_secret = os.getenv("SERP_API_KEY")

client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", openai_api_key))


def run_conversation():
    # Step 1: send the conversation and available functions to the model
    messages = []
    messages.append({"role": "system", "content": "You are allowed to generate search_query text on Financial Industries such as Dividends, Earnings per share/EPS etc. and plug into functions.  Provide Answer with Reference link from function in the format: [Answer](URL)"})
    messages.append({"role": "user", "content": "What's the last quarter dividend price declared by Scotiabank in Q1 2024?"})
    tools = [
         {
        "type": "function",
        "function": {
            "name": "search_internet",
            "description": "Search the internet for the search_query on Finance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_query": {
                        "type": "string",
                        "description": "The query to search for on the internet."
                    }
                },
                "required": ["search_query"]
            }
        }
    }
    ]
    response = client.chat.completions.create(
        model=fine_tuned_model_id,
        messages=messages,
        tools=tools,
        tool_choice="auto",  # auto is default, but we'll be explicit
    )
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    # Step 2: check if the model wanted to call a function
    if tool_calls:
        print('+++++++++++Invoking function++++++++')
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        available_functions = {
            "search_internet": search_internet,
        }  # only one function in this example, but you can have multiple
        messages.append(response_message)  # extend conversation with assistant's reply
        # Step 4: send the info for each function call and function response to the model
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            print('function to call -->',function_to_call)
            function_args = json.loads(tool_call.function.arguments)
            print('function to call w/ arguments-->',function_args)
            function_response = function_to_call(
                search_query=function_args.get("search_query")
            )
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )  # extend conversation with function response
        second_response = client.chat.completions.create(
            model=fine_tuned_model_id,
            messages=messages,
        )  # get a new response from the model where it can see the function response
        return second_response
    
# Example dummy function hard coded to return the same weather
# In production, this could be your backend API or an external API
def search_internet(search_query):
    """Get the latest news from the internet on Finance for given search_query"""
    if search_query == None:
        print("LLM Didn't pass the argument")
        return
    params = {
    "engine": "google",
    "q": search_query,
    "api_key": serp_api_secret

    }
    print('--------------')
    print(params)
    print('--------------')
    search = GoogleSearch(params)
    results = search.get_dict()
    print('--------------')
    print(results)
    print('--------------')
    organic_results = results["organic_results"][:3]

    # Extract 'link' and 'snippet' fields from each dictionary
    filtered_data = [{'link': item['link'], 'snippet': item['snippet']} for item in organic_results]

    # Convert the filtered data to JSON
    return json.dumps(filtered_data, indent=4)

def run():

    # # Setting page title and header
    st.set_page_config(page_title="Codi", page_icon=":robot_face:")
    st.markdown("<h1 style='text-align: center;'>Codi</h1>", unsafe_allow_html=True)

    
    #  # Load and display image
    image = "./assets/images/codi.png"  # Replace "your_image_path.jpg" with the path to your image file

    st.markdown("<img src='https://i.postimg.cc/VNDMshSr/codi.png' width='100' height='100' style='display: block; margin: 0 auto;'>" , unsafe_allow_html=True)

    st.markdown("<h4 style='text-align: center;'>How can I help you today?</h4>", unsafe_allow_html=True)
    
    system_message = """You are Fine-tuned on following 3 tasks:
    1. Queue Task - You will be provided queries from 'Direct Investing' customer service department at RBC. Classify each query to the right queue category.\nProvide your output in a bullet point format with only one: Queue Category\nQueue Categories are:\n--Queue 1: Account Management\n--Queue 2: Fund Transfer\n--Queue 3: External Transfers\n--Queue 4: Trading and Withdrawals"

    2. Transactional Task - You are given with the transactional data and your task is to process this tabular data containing both text and numerical values based on criteria then generate answers.\n-The answers should be in bullets and sub-bullet points\n-If the answer cannot be found in the Transactional data given below, write 'please contact RBC Direct Investing Team.'\nTransactional Data :\n| Account No | Request Date | Transactional Details | Transfer Date | Withdrawal Amount | Deposit Amount | Balance Amount | Expected Transfer Days | Status | Note | Last Note Date |\n|------------|--------------|---------------------|---------------|----------------|-------------|-------------|-----------------------|--------|------|----------------|\n| 123456 | 2024-01-05 | Transferred cash from TD Bank to RBC | 2024-02-14 | - | 75000 | 150000 | 10 | Opened | Contacted customer to confirm transaction | 2024-02-14 |\n| 789012 | 2024-01-10 | Transferred funds from CIBC to RBC | 2024-01-25 | - | 100000 | 200000 | 15 | Opened | Resolved missing withdrawal transaction information | 2024-01-25 |\n| 345678 | 2024-01-15 | Withdrew cash for investment | 2024-02-05 | 50000 | - | 150000 | - | Closed | - | - |\n| 901234 | 2024-01-20 | Deposited funds from BMO into account | 2024-02-07 | - | 85000 | 185000 | 18 | Opened | Verified deposit with customer | 2024-02-07 |\n| 567890 | 2024-01-25 | Transferred money from RBC to TD Bank | 2024-02-10 | - | 60000 | 160000 | 16 | Opened | Sent confirmation email to customer | 2024-02-10 |\n| 234567 | 2024-02-03 | Withdrew funds for stock purchase | 2024-02-25 | 70000 | - | 160000 | - | Closed | - | - |\n| 890123 | 2024-02-08 | Transferred cash from ScotiaBank to RBC | 2024-02-28 | - | 95000 | 195000 | 20 | Opened | Called customer on the same day | 2024-02-28 |\n| 456789 | 2024-02-12 | Deposited funds from RBC into account | 2024-03-06 | - | 80000 | 180000 | 22 | Opened | Resolved deposit discrepancy | 2024-03-06 |\n| 123456 | 2024-02-18 | Withdrew cash for investment | 2024-03-12 | 45000 | - | 135000 | - | Closed | -

    3. Customer Service QnA Task - You will be provided queries from customer service department. Your task is to answer the question using only the provided steps with reference at the end. If the document does not contain the information needed to answer this question then write: 'Insufficient information, please contact RBC Direct Investing customer service representative at 1-800-769-2560.

    --You are allowed to generate search_query text on Financial Industries such as Dividends, Earnings per share/EPS etc. and plug into functions.  Provide Answer with Reference link from function in the format: [Answer](URL)"
    """
    

    
    
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", openai_api_key))

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = fine_tuned_model_id

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        if message["role"] != "system":  # Check if message role is not system
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Message Codi...."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:    
                stream = client.chat.completions.create(
                    model=st.session_state["openai_model"],
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    stream=True,
                )
                response = st.write_stream(stream)
            except Exception as e:
                st.write("Maximum Token's limit reached. Please refresh the Page.")
                st.stop()
                
        #st.session_state.messages.append({"role": "system", "content": system_message})
        st.session_state.messages.append({"role": "assistant", "content": response})
   
    # Adding a system message without rendering it
    st.session_state.messages.append({"role": "system", "content": system_message})

if __name__ == "__main__":
    run()