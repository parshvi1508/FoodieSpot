# Main Streamlit entry point
# src/app.py
import streamlit as st
from ai.agent import ReservationAgent

agent = ReservationAgent()

st.title("FoodieSpot AI Reservations")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("How can I help?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    response = agent.generate_response(prompt)
    st.session_state.messages.append({"role": "assistant", "content": response})

def show_restaurant(restaurant):
    st.subheader(restaurant['name'])
    cols = st.columns(3)
    cols[0].metric("Cuisine", restaurant['cuisine'])
    cols[1].metric("Capacity", restaurant['capacity'])
    cols[2].button("Book Now", key=restaurant['id'])
