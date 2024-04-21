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
    
    # fine tune model id
    fine_tuned_model_id='ft:gpt-3.5-turbo-0125:personal:di-txn-assist:9GCDhNRR'

    

    
    
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", openai_api_key))

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = fine_tuned_model_id

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Message Codi...."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    run()