import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import plotly.express as px
import os

st.set_page_config(
    page_title="AI Data Analytics Agent",
    page_icon="📊",
    layout="wide"
)
# =========================
# Gemini Configuration
# =========================

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel("gemini-2.5-flash")
st.write("Gemini configured successfully")
if "history" not in st.session_state:
    st.session_state.history = []

# =========================
# SQL Generation Function
# =========================

def generate_sql(question, columns):

    prompt = f"""
    You are an expert SQLite analyst.

    Table name: data

    Available columns:
    {columns}

    IMPORTANT:
    1. Use only the columns provided.
    2. Do not invent column names.
    3. Return ONLY SQL.
    4. No explanation.
    5. No markdown.

    Question:
    {question}
    """

    response = model.generate_content(prompt)

    sql_query = response.text.strip()

    # Remove markdown if Gemini adds it
    sql_query = sql_query.replace("```sql", "")
    sql_query = sql_query.replace("```", "")
    sql_query = sql_query.strip()

    return sql_query

def create_chart(df):

    if len(df.columns) == 2:

        fig = px.bar(
            df,
            x=df.columns[0],
            y=df.columns[1],
            title="Analysis Results"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )
# =========================
# Streamlit UI
# =========================
def generate_insights(question, result):

    prompt = f"""
    You are a Senior Data Analyst.

    Business Question:
    {question}

    Query Results:
    {result.to_string(index=False)}

    Provide:

    1. Key Findings
    2. Business Insights
    3. Recommendations

    Keep it concise and professional.
    """

    response = model.generate_content(prompt)

    return response.text


st.title("📊 AI-Powered Data Analytics Agent")

st.markdown("""
Upload any CSV dataset and analyze it using natural language.

### Features
✅ Upload Any CSV Dataset  
✅ AI SQL Query Generation  
✅ Interactive Charts  
✅ AI Business Insights  
✅ Download Results
""")

st.sidebar.title("📊 AI Data Analytics Agent")

st.sidebar.info("""
Ask questions about your dataset in plain English.

Examples:
• Show total sales by category
• Show top 10 products by sales
• Which region generated highest profit?
• Show average discount by category
""")

st.sidebar.subheader("📝 Query History")

for q in st.session_state.history:
    st.sidebar.write("•", q)

uploaded_file = st.file_uploader(
    "📂 Upload CSV File",
    type=["csv"]
)

# =========================
# Process Uploaded File
# =========================

if uploaded_file is not None:

    try:
        df = pd.read_csv(uploaded_file, encoding="latin1")

    except Exception:
        df = pd.read_csv(uploaded_file)

    # Create SQLite database
    conn = sqlite3.connect(":memory:")

    # Save dataframe into SQL table
    df.to_sql(
        "data",
        conn,
        if_exists="replace",
        index=False
    )

    st.success("✅ Dataset Uploaded Successfully!")

    st.subheader("Dataset Preview")
    st.dataframe(df.head())
    
    st.write("Rows:", df.shape[0])
    st.write("Columns:", df.shape[1])

    st.subheader("Detected Columns")
    st.write(df.columns.tolist())

    # =========================
    # Question Box
    # =========================

    st.subheader("Ask Questions About Your Data")

    question = st.text_input(
        "Enter your question:"
    )

    # =========================
    # Run Query Button
    # =========================

    if st.button("Run Query"):

        if question.strip() == "":
            st.warning("Please enter a question.")
            st.stop()
        st.session_state.history.append(question)
        try:

            columns = df.columns.tolist()

            sql_query = generate_sql(
                question,
                columns
            )

            st.subheader("Generated SQL")
            st.code(sql_query)

            result = pd.read_sql_query(
                sql_query,
                conn
            )

            st.subheader("Results")
            st.dataframe(result)
            create_chart(result)
            st.subheader("📈 AI Business Insights")

            insights = generate_insights(
                 question,
                 result
            )

            st.write(insights)
            # Download Results
            csv = result.to_csv(index=False)

            st.download_button(
                label="📥 Download Results",
                data=csv,
                file_name="results.csv",
                mime="text/csv"
            )

        except Exception as e:
            st.error(f"Error: {e}")