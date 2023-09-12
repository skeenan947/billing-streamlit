# Simplifying Database Interactions with Language Models: A Guide to Using LangChain and BigQuery

Interacting with SQL databases can be a challenging task, especially for those without extensive SQL knowledge. However, with the advent of language models like LangChain, you can simplify the process and make database interactions more accessible. In this blog post, we'll explore a Python script that uses LangChain to generate SQL queries and interacts with Google BigQuery. This approach can be applied to any SQL database, making it a powerful tool for data analysis and querying.

## The Power of Language Models

Language models have gained significant attention for their ability to understand and generate human-like text. LangChain, in particular, is a versatile language model that can assist in formulating SQL queries based on user prompts. This opens up opportunities for users to interact with SQL databases without the need for extensive SQL expertise.

## Understanding the Code

The provided Python code demonstrates how to harness the capabilities of LangChain to simplify database interactions. Here's a breakdown of the key components:

```python
import streamlit as st
import os
from langchain.llms import VertexAI  # LangChain
from google.cloud import bigquery
import logging

os.environ['GOOGLE_CLOUD_PROJECT'] = 'g-playground-1'

# Function to process user's query
def process_prompt():
    user_query = st.session_state.user_query
    st.chat_message("user").write(user_query)
    dataset = 'g-playground-1.internal_billing_dataset.gcp_billing_export_v1_010767_AD0D5D_BCC8F6'

    with open("schema.json", "r") as f:
        schema = f.read()

    with open("prompt.txt", "r") as f:
        prompt = f.read()
    template = prompt.format(schema=schema, question=user_query, dataset=dataset)

    llm = VertexAI(model_name="code-bison", max_output_tokens=2048)
    sql = llm(prompt=template).replace("```", "").replace("sql", "")
    st.chat_message("assistant").write("Running query... \n```\n{}\n```".format(sql))
    out = run_query(sql)
    st.bar_chart(out)
    st.write(out)

# Function to execute SQL queries
def run_query(bq_query):
    res = []
    client = bigquery.Client(os.environ['GOOGLE_CLOUD_PROJECT'])
    q = bq_query.replace('`', '')
    if 'SELECT' not in q:
        rows = [q]
    else:
        try:
            query_job = client.query(q)
            rows = query_job.to_dataframe()
            if 'month' in rows.columns:
                rows.set_index('month', inplace=True)
            if 'day' in rows.columns:
                rows.set_index('day', inplace=True)
            if 'year' in rows.columns:
                rows.set_index('year', inplace=True)
        except Exception as e:
            logging.error(e)
    return rows

# User input using Streamlit
user_query = st.chat_input("Ask me a question about your bill", on_submit=process_prompt, key="user_query")
```

### 1. Setting the Environment

```python
os.environ['GOOGLE_CLOUD_PROJECT'] = 'g-playground-1'
```

In this line, we set the Google Cloud project environment variable to 'g-playground-1' to ensure the code connects to the correct project. However, this step can be adapted to any database environment.

### 2. The `process_prompt()` Function

The core functionality of the code is encapsulated in the `process_prompt()` function, which performs the following steps:

- Captures the user's query.
- Reads the database schema and a user prompt template.
- Utilizes LangChain (VertexAI in this case) to generate an SQL query based on the user's input, schema, and other relevant information.
- Executes the generated SQL query on the database (BigQuery in this example) and visualizes the results using Streamlit widgets.

### 3. Query Execution with `run_query()`

The `run_query()` function handles the connection to the SQL database, submits the SQL query, and returns the results. It also includes minor adjustments to the query text for smoother execution.

### 4. Streamlit User Interaction

The code allows users to input their questions or queries using a Streamlit chat input widget. When the user submits a query, the `process_prompt()` function is called to generate and execute the SQL query, and the results are presented using Streamlit's visualization capabilities.

## Using the Code with Any SQL Database

The beauty of this approach is its adaptability to any SQL database. To apply this code to your database, follow these general steps:

1. Ensure you have the required Python libraries installed, including Streamlit, the appropriate database driver, and LangChain.
2. Configure your database connection parameters, ensuring compatibility with the chosen database.
3. Save your database schema in a file (e.g., "schema.json") and create a user prompt template.
4. Customize the code by replacing the LangChain model and adjusting other configuration parameters as needed.
5. Execute the code.
6. Interact with the Streamlit interface by entering questions or queries related to your database.

## Conclusion

Interacting with SQL databases can be simplified and made more accessible through the use of language models like LangChain. This Python script demonstrates how to leverage LangChain's capabilities to generate SQL queries based on user prompts and interact with databases, such as Google BigQuery. Whether you're a data analyst, developer, or someone curious about databases, this approach can enhance your ability to harness the power of SQL databases for data analysis and exploration, regardless of your SQL expertise.