import streamlit as st
import os
from langchain.llms import VertexAI #LlamaCpp
from google.cloud import bigquery
import logging
import pandas

os.environ['GOOGLE_CLOUD_PROJECT']='g-playground-1'


def process_prompt():
    user_query = st.session_state.user_query
    st.chat_message("user").write(user_query)
    dataset = 'g-playground-1.internal_billing_dataset.gcp_billing_export_v1_010767_AD0D5D_BCC8F6'
    schema = ""
    with open("schema.json", "r") as f:
        schema = f.read()

    with open("prompt.txt", "r") as f:
        prompt = f.read()
    template = prompt.format(schema=schema, question=user_query, dataset=dataset)

    # Use for Llama
    # n_gpu_layers = 40  # Change this value based on your model and your GPU VRAM pool.
    # n_batch = 512  # Should be between 1 and n_ctx, consider the amount of VRAM in your GPU.
    # Make sure the model path is correct for your system!
    #llm = LlamaCpp(
    #    model_path="./llama-2-7b-chat.ggmlv3.q4_0.bin",
    #    n_gpu_layers=n_gpu_layers,
    #    n_batch=n_batch,
    #    verbose=True,
    #)
    llm = VertexAI(model_name="code-bison", max_output_tokens=2048)
    # in case it decides to spit out markdown-formatted SQL instead of straight SQL
    sql = llm(prompt = template).replace("```", "").replace("sql", "")
    st.chat_message("assistant").write("Running query... \n```\n{}\n```".format(sql))
    out = run_query(sql)
    st.bar_chart(out)

    st.write(out)

def run_query(bq_query):
    res = []
    client = bigquery.Client(os.environ['GOOGLE_CLOUD_PROJECT'])
    # Perform a query.
    # if the data was returned with `s then remove them
    q = bq_query.replace('`', '')
    if 'SELECT' not in q:
        # if the result was not a query, send it back to the customer - it's probably already what they asked for
        rows = [q]
    else:
        try:
            query_job = client.query(q)  # API request
            rows = query_job.to_dataframe()  # Waits for query to finish
            if 'month' in rows.columns:
                rows.set_index('month', inplace=True)
            if 'day' in rows.columns:
                rows.set_index('day', inplace=True)
            if 'year' in rows.columns:
                rows.set_index('year', inplace=True)
        except Exception as e:
            logging.error(e)
    return rows


user_query = st.chat_input("Ask me a question about your bill", on_submit=process_prompt, key="user_query")
