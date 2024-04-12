import streamlit as st

# Section 1
with st.container():
    st.header("Section 1")
    if "button_clicked1" not in st.session_state:
        st.session_state.button_clicked = False

    if st.button("Click me1"):
        st.session_state.button_clicked = True

    if st.session_state.button_clicked:
        st.write("Button clicked1")

# Section 2
with st.container():
    st.header("Section 2")
    if "button_clicked2" not in st.session_state:
        st.session_state.button_clicked = False

    if st.button("Click me2"):
        st.session_state.button_clicked = True

    if st.session_state.button_clicked:
        st.write("Button clicked2")

# Section 3
with st.container():
    st.header("Section 3")
    if "button_clicked3" not in st.session_state:
        st.session_state.button_clicked = False

    if st.button("Click me3"):
        st.session_state.button_clicked = True

    if st.session_state.button_clicked:
        st.write("Button clicked3")

# Section 4
with st.container():
    st.header("Section 4")

    # Initialize the button state
    if "button_clicked4" not in st.session_state:
        st.session_state.button_clicked4 = 0

    # When the button is clicked, increment the state
    if st.button("Click me4"):
        st.session_state.button_clicked4 += 1

    # Print the current state
    st.write(f"Current state: {st.session_state.button_clicked4}")

    # If the button has been clicked an odd number of times, show the text
    if st.session_state.button_clicked4 % 2 == 1:
        st.write("Button clicked4")

    # Section 5
    pop = st.popover("Button label")
    pop.checkbox("Show all")

    st.balloons()
    st.snow()
    st.toast("Warming up...")
    st.error("Error message")
    st.warning("Warning message")
    st.info("Info message")
    st.success("Success message")
    st.exception(RuntimeError("This is an exception of type RuntimeError"))
