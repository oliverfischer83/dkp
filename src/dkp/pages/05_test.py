import streamlit as st

# Create a checkbox
checkbox = st.checkbox('Check me to enable the button')

# Create a button, but only if the checkbox is checked
if checkbox:
    if st.button('Enabled Button'):
        st.write('Button clicked!')
else:
    st.write('Check the box to enable the button')