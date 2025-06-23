import asyncio
import json
import requests
import gradio as gr

from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentExecutor
from langchain.agents.router import RouterAgent
from langchain.tools import StructuredTool

API_URL = "http://localhost:8000"

# Endpoint wrappers

def predict_restock(sku_id: str, days_history: int, current_stock: int, lead_time_days: int, service_level_pct: float, budget_currency: str):
    payload = {
        "sku_id": sku_id,
        "days_history": days_history,
        "current_stock": current_stock,
        "lead_time_days": lead_time_days,
        "service_level_pct": service_level_pct,
        "budget_currency": budget_currency,
    }
    r = requests.post(f"{API_URL}/predict-restock", json=payload)
    return r.json()

def optimize_markdown(sku_id: str, current_price: float, current_stock: int):
    payload = {
        "sku_id": sku_id,
        "current_price": current_price,
        "current_stock": current_stock,
    }
    r = requests.post(f"{API_URL}/optimize-markdown", json=payload)
    return r.json()

def liquidate():
    r = requests.post(f"{API_URL}/liquidate")
    return r.json()

llm = ChatOpenAI(temperature=0)

tools = [
    StructuredTool.from_function(predict_restock, name="predict_restock"),
    StructuredTool.from_function(optimize_markdown, name="optimize_markdown"),
    StructuredTool.from_function(liquidate, name="liquidate"),
]

router = RouterAgent.from_llm_and_tools(llm=llm, tools=tools)
agent = AgentExecutor(agent=router, tools=tools, verbose=True)

async def chat_fn(history, message):
    result = await agent.ainvoke(message)
    history.append((message, json.dumps(result)))
    return history, ""

def main():
    with gr.Blocks() as demo:
        chatbot = gr.Chatbot()
        msg = gr.Textbox()
        clear = gr.Button("Clear")

        def reset():
            return [], ""

        msg.submit(chat_fn, [chatbot, msg], [chatbot, msg])
        clear.click(reset, outputs=[chatbot, msg])

    demo.launch()

if __name__ == "__main__":
    main()
