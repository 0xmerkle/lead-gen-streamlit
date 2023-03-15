import streamlit as st

from langchain.sql_database import SQLDatabase
from langchain.llms.openai import OpenAI
from requests import get, post
from langchain.agents import AgentExecutor, load_tools, initialize_agent, Tool
from langchain.tools.python.tool import PythonREPLTool
from langchain.agents.agent_toolkits import create_python_agent
from langchain.python import PythonREPL
from langchain import SerpAPIWrapper
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains import SimpleSequentialChain
from langchain.chains import LLMChain

from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

load_dotenv()

import os

open_ai_key = os.environ.get("OPENAI_API_KEY")
os.environ["SERPAPI_API_KEY"] = os.environ.get("SERPAPI_API_KEY")


def execute_query(query):
    search = SerpAPIWrapper()
    tools = [
        Tool(
            name="Search",
            func=search.run,
            description="useful for when you need to answer questions about current events",
        )
    ]
    llm = OpenAI(temperature=0, openai_api_key=open_ai_key)

    tools = load_tools(["serpapi", "llm-math"], llm=llm)
    agent = initialize_agent(
        tools, llm, agent="zero-shot-react-description", verbose=True
    )

    r = agent.run(query)
    return r


memory = ConversationBufferMemory(memory_key="chat_history")


def scrape(urls):
    print("urks", urls)
    for url in urls:
        response = requests.get(url, verify=True)
        soup = BeautifulSoup(response.text, "html.parser")
        contact_info = soup.find("div", {"class": "contact-info"})
        print(contact_info)
        return contact_info


def find_and_save_leads(query):
    python = PythonREPL()
    tools = [
        Tool(
            name="Scrape",
            func=lambda urls: scrape(urls),
            description="function to scrape websites with python when you provide the exact url links",
        )
    ]
    tool = Tool(
        name="Scrape",
        func=lambda urls: scrape(urls),
        description="useful for when you need to scrape websites with python",
    )
    llm = OpenAI(temperature=0, openai_api_key=open_ai_key)

    tools = load_tools(["serpapi", "python_repl"], llm=llm)
    # tools.append(tool)
    agent = initialize_agent(
        tools, llm, agent="zero-shot-react-description", memory=memory, verbose=True
    )
    r = agent.run(query)
    return r


def find_leads(query):
    llm = OpenAI(temperature=0.3, openai_api_key=open_ai_key)
    template = """You are an expert in scraping websites with python.
    Use your expertise to scrape the following websites for {contact}.
    You can use the python REPL to find the tools.

    Websites: {websites}
    Era: {era}
    Playwright: This is a synopsis for the above play:"""
    prompt_template = PromptTemplate(
        input_variables=["websites", "emails"], template=template
    )


st.header("Dune SQL Generator")

user_input = st.text_input("Enter your SQL query here")

if "memory" not in st.session_state:
    st.session_state["memory"] = ""

if st.button("Generate Dune SQL"):
    st.markdown(find_and_save_leads(user_input))
    st.session_state["memory"] += memory.buffer
    print(st.session_state["memory"])

# emails = []
#               for url in urls.values():
#                   response = requests.get(url)
#                   soup = BeautifulSoup(response.text, 'html.parser')
#                   for link in soup.find_all('a'):
#                       if 'mailto:' in link.get('href'):
#                           emails.append(link.get('href').split(':')[1])
#               with open('emails.csv', 'w', newline='') as csvfile:
#                   writer = csv.writer(csvfile)
#                   writer.writerow(['Website', 'Email'])
#                   for url, email in zip(urls.values(), emails):
#                       writer.writerow([url, email])
