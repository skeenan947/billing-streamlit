import streamlit as st
import os
from langchain.llms import VertexAI #LlamaCpp
from google.cloud import bigquery
import logging
import pandas

os.environ['GOOGLE_CLOUD_PROJECT']='g-playground-1'


def process_prompt():
    user_query = st.session_state.user_query
    dataset = 'g-playground-1.internal_billing_dataset.gcp_billing_export_v1_010767_AD0D5D_BCC8F6'
    schema = ""
    with open("schema.json", "r") as f:
        schema = f.read()

    template = """Given schema: {schema}
    where service.id is an unusable identifier and service.description is the name of the service
    FORMAT is not a valid keyword in bigquery
    use invoice.month for any data prior to the current month
    INTERVAL must be in days, not months or years

    input: write a BQ SQL query: how much did I spend on compute in the last 90 days?
    output: SELECT
        sum(total_cost) as my_cost,
        FORMAT_DATE("%Y-%m", usage_start_time) AS month,
    FROM `{dataset}`
        WHERE service.description LIKE "%Compute%"
        AND usage_start_time >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), MONTH) - INTERVAL 90 day
    GROUP BY month
    
    input: write a BQ SQL query: how much did I spend in the last month?
    output: SELECT
        sum(total_cost) as my_cost,
        FORMAT_DATE("%Y-%m", usage_start_time) AS month
    FROM `{dataset}`
        WHERE usage_start_time >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), MONTH) - INTERVAL 30 day
    GROUP BY month

    input: write a BQ SQL query: how much did I spend last month?
    output: SELECT
        sum(total_cost) as my_cost,
        FORMAT_DATE("%Y-%m", usage_start_time) AS month
    FROM `{dataset}`
        WHERE usage_start_time >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), MONTH) - INTERVAL 60 day
        AND usage_start_time <= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), MONTH) - INTERVAL 30 day
    GROUP BY month

    input: write a BQ SQL query: how much did I spend on compute over the last 6 months?
    output: SELECT
        sum(cost) as my_cost,
        FORMAT_DATE("%Y-%m", usage_start_time) AS month
    FROM `{dataset}`
    WHERE service.description LIKE "%Compute Engine%" 
    AND usage_start_time >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), MONTH) - INTERVAL 180 day

    input: write a BQ SQL query: How much did I spend on vertex in the last month?
    output: SELECT SUM(cost) AS total_cost 
    FROM `{dataset}`
    WHERE service.description LIKE "%Vertex% 
    AND usage_start_time >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), MONTH) - INTERVAL 30 day

    input: write a BQ SQL query: How much did I spend on BQ over the last 6 months?
    output: SELECT SUM(cost) AS total_cost,
    FORMAT_DATE("%Y-%m", usage_start_time) AS month
    FROM `{dataset}`
    WHERE service.description LIKE "%BigQuery%"
    AND usage_start_time >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), MONTH) - INTERVAL 180 day

    input: Write a BQ SQL query: How much did I spend on compute this quarter?
    output: SELECT
        sum(cost) as my_cost,
        FORMAT_DATE("%Y-%m", usage_start_time) AS month
    FROM `g-playground-1.internal_billing_dataset.gcp_billing_export_v1_010767_AD0D5D_BCC8F6`
    WHERE service.description LIKE "%Compute Engine%" 
    AND usage_start_time >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), QUARTER) - INTERVAL 90 day
    GROUP BY month

    input: write a BQ SQL query: {question}
    output:""".format(schema=schema, question=user_query, dataset=dataset)

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
    st.write("Running query... \n```\n{}\n```".format(sql))
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
