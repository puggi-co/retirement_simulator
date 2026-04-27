import streamlit as st
from src.io.portfolio_loader import get_portfolio_from_streamlit

form_data = {
    "account_name": st.text_input("Account Name"),
    "account_type": st.selectbox("Account Type", ["ira", "brokerage", "inc_ssa"]),
    "base_balance": st.number_input("Base Balance", min_value=0.0),
    "distribution_age": st.number_input("Distribution Age", min_value=0),
    "filing_status": st.selectbox("Filing Status", ["single", "married"]),
    # Add other required fields here...
}

if st.button("Submit Portfolio"):
    df = get_portfolio_from_streamlit(form_data)
    st.dataframe(df)
