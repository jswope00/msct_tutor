import openai
import google.generativeai as generativeai
import anthropic
import os
import importlib
from dotenv import load_dotenv
import re
import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from streamlit_extras.let_it_rain import rain

load_dotenv()

from config import *

if "CURRENT_PHASE" not in st.session_state:
    st.session_state['additional_prompt'] = ""
    st.session_state['chat_history'] = []
    st.session_state['CURRENT_PHASE'] = 0
    st.session_state['TOTAL_PRICE'] = 0

def randomize_key():
    return random.choice(list(DISEASE_GENERATOR.keys()))

if "random_key" not in st.session_state:
    st.session_state["random_key"] = randomize_key()

st.session_state["random_key"] = randomize_key()


openai.api_key = os.getenv("MSCT_API_KEY")
gemini_api_key = os.getenv('GOOGLE_API_KEY')
claude_api_key = os.getenv('CLAUDE_API_KEY')

user_input = {}
function_map = {
    "text_input": st.text_input,
    "text_area": st.text_area,
    "warning": st.warning,
    "button": st.button,
    "radio": st.radio,
    "markdown": st.markdown,
    "selectbox": st.selectbox,
    "checkbox": st.checkbox,
    "slider": st.slider,
    "number_input": st.number_input,
    "image": st.image
}


def build_field(phase_name, fields):
    for field_key, field in fields.items():
        field_type = field.get("type", "")
        field_label = field.get("label", "")
        field_body = field.get("body", "")
        field_value = field.get("value", "")
        field_index = field.get("index",None)
        field_max_chars = field.get("max_chars", None)
        field_help = field.get("help", "")
        field_on_click = field.get("on_click", None)
        field_options = field.get("options", [])
        field_horizontal = field.get("horizontal", False)
        field_min_value = field.get("min_value",None)
        field_max_value = field.get("max_value",None)
        field_step = field.get("step",None)
        field_height = field.get("height", None)
        field_unsafe_html = field.get("unsafe_allow_html", False)
        field_placeholder = field.get("placeholder", "")
        field_image = field.get("image", "")
        field_caption = field.get("caption", "")

        kwargs = {}
        if field_label:
            kwargs['label'] = field_label
        if field_body:
            kwargs['body'] = field_body
        if field_value:
            kwargs['value'] = field_value
        if field_index:
            kwargs['index'] = field_index
        if field_options:
            kwargs['options'] = field_options
        if field_max_chars:
            kwargs['max_chars'] = field_max_chars
        if field_help:
            kwargs['help'] = field_help
        if field_on_click:
            kwargs['on_click'] = field_on_click
        if field_horizontal:
            kwargs['horizontal'] = field_horizontal
        if field_min_value:
            kwargs['min_value'] = field_min_value
        if field_max_value:
            kwargs['max_value'] = field_max_value
        if field_step:
            kwargs['step'] = field_step
        if field_height:
            kwargs['height'] = field_height
        if field_unsafe_html:
            kwargs['unsafe_allow_html'] = field_unsafe_html
        if field_placeholder:
            kwargs['placeholder'] = field_placeholder
        if field_image:
            kwargs['image'] = field_image
        if field_caption:
            kwargs['caption'] = field_caption


        key = f"{phase_name}_phase_status"

        # If the user has already answered this question:
        if key in st.session_state and st.session_state[key]:
            # Write their answer
            if f"{phase_name}_user_input_{field_key}" in st.session_state:
                if field_type != "selectbox":
                    kwargs['value'] = st.session_state[f"{phase_name}_user_input_{field_key}"]
                kwargs['disabled'] = True

        my_input_function = function_map[field_type]

        with stylable_container(
                key="large_label",
                css_styles="""
                label p {
                    font-weight: bold;
                    font-size: 16px;
                }

                div[role="radiogroup"] label p{
                    font-weight: unset !important;
                    font-size: unset !important;
                }
                """,
        ):
            user_input[field_key] = my_input_function(**kwargs)


def call_openai_completions(phase_instructions, user_prompt, image_url=None):
    selected_llm = st.session_state['selected_llm']
    llm_configuration = st.session_state['llm_config']
    chat_history = st.session_state["chat_history"]

    if image_url and selected_llm not in ["gpt-4-turbo", "gpt-4o"]:
        return "ERROR: This model does not support image recognition"

    message_history = []
    message_history_gemini = []
    if len(chat_history) > 0:
        for history in chat_history:
            user_content = history["user"]
            assistant_content = history["assistant"]
            message_history.extend(
                [{"role": "user", "content": user_content}, {"role": "assistant", "content": assistant_content}])
            message_history_gemini.extend(
                [{"role": "user", "parts": [user_content]}, {"role": "model", "parts": [assistant_content]}])
    if image_url:
        messages_openai = [
                        {"role": "system", "content": SYSTEM_PROMPT + "\n" + phase_instructions},
                        {"role": "user", "content": [{"type": "image_url", "image_url": {"url": image_url}}]},
                        {"role": "user", "content": user_prompt}
                    ]
    else:
        messages_openai = [
                {"role": "system", "content": SYSTEM_PROMPT + "\n" + phase_instructions},
                {"role": "user", "content": user_prompt}
            ]
    if selected_llm in ["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4o"]:
        try:
            response = openai.chat.completions.create(
                model=llm_configuration["model"],
                messages= message_history+messages_openai,
                max_tokens=llm_configuration.get("max_tokens", 1000),
                temperature=llm_configuration.get("temperature", 1),
                top_p=llm_configuration.get("top_p", 1),
                frequency_penalty=llm_configuration.get("frequency_penalty", 0),
                presence_penalty=llm_configuration.get("presence_penalty", 0)
            )
            input_price = int(response.usage.prompt_tokens) * llm_configuration["price_input_token_1M"] / 1000000
            output_price = int(response.usage.completion_tokens) * llm_configuration[
                "price_output_token_1M"] / 1000000
            total_price = input_price + output_price
            st.session_state['TOTAL_PRICE'] += total_price
            return response.choices[0].message.content
        except Exception as e:
            st.write(f"**OpenAI Error Response:** {selected_llm}")
            st.error(f"Error: {e}")
    if selected_llm in ["gemini-1.0-pro", "gemini-1.5-flash", "gemini-1.5-pro"]:
        try:
            generativeai.configure(api_key=gemini_api_key)
            generation_config = {
                "temperature": llm_configuration["temperature"],
                "top_p": llm_configuration.get("top_p", 1),
                "max_output_tokens": llm_configuration.get("max_tokens", 1000),
                "response_mime_type": "text/plain",
            }
            model = generativeai.GenerativeModel(
                llm_configuration["model"],
                generation_config=generation_config,
                system_instruction=SYSTEM_PROMPT + "\n" + phase_instructions,
            )
            chat_session = model.start_chat(
                history= message_history_gemini
            )
            gemini_response = chat_session.send_message(user_prompt)
            gemini_response_text = gemini_response.text

            return gemini_response_text
        except Exception as e:
            st.write("**Gemini Error Response:**")
            st.error(f"Error: {e}")
    if selected_llm in ["claude-opus", "claude-sonnet", "claude-haiku", "claude-3.5-sonnet"]:
        try:
            client = anthropic.Anthropic(api_key=claude_api_key)
            anthropic_response = client.messages.create(
                model=llm_configuration["model"],
                max_tokens=llm_configuration["max_tokens"],
                temperature=llm_configuration["temperature"],
                system=SYSTEM_PROMPT + "\n" + phase_instructions,
                messages= message_history+[
                    {"role": "user", "content": [{"type": "text", "text": user_prompt}]},
                ]
            )
            input_price = int(anthropic_response.usage.input_tokens) * llm_configuration[
                "price_input_token_1M"] / 1000000
            output_price = int(anthropic_response.usage.output_tokens) * llm_configuration[
                "price_output_token_1M"] / 1000000
            total_price = input_price + output_price
            response_cleaned = '\n'.join([block.text for block in anthropic_response.content if block.type == 'text'])
            st.session_state['TOTAL_PRICE'] += total_price
            return response_cleaned
        except Exception as e:
            st.write(f"**Anthropic Error Response: {selected_llm}**")
            st.error(f"Error: {e}")


def format_user_prompt(prompt, user_input, phase_name=None):
    try:
        prompt = prompt_conditionals(prompt, user_input, phase_name)
        formatted_user_prompt = prompt.format(**user_input)
        return formatted_user_prompt
    except:
        formatted_user_prompt = prompt.format(**user_input)
        return formatted_user_prompt


def st_store(input, phase_name, phase_key, field_key=""):
    if field_key:
        key = f"{phase_name}_{field_key}_{phase_key}"
    else:
        key = f"{phase_name}_{phase_key}"
    st.session_state[key] = input


def build_scoring_instructions(rubric):
    scoring_instructions = f"""
    Please score the user's previous response based on the following rubric: \n{rubric}
    \n\nPlease output your response as JSON, using this format: {{ "[criteria 1]": "[score 1]", "[criteria 2]": "[score 2]", "total": "[total score]" }}
    """
    return scoring_instructions


def extract_score(text):
    pattern = r'"total":\s*"?(\d+)"?'
    match = re.search(pattern, text)
    if match:
        return int(match.group(1))
    else:
        return 0


def check_score(PHASE_NAME):
    score = st.session_state[f"{PHASE_NAME}_ai_score"]
    try:
        if score >= PHASES[PHASE_NAME]["minimum_score"]:
            st.session_state[f"{PHASE_NAME}_phase_status"] = True
            return True
        else:
            st.session_state[f"{PHASE_NAME}_phase_status"] = False
            return False
    except:
        st.session_state[f"{PHASE_NAME}_phase_status"] = False
        return False


def skip_phase(PHASE_NAME, No_Submit=False):
    phase_fields = PHASES[PHASE_NAME]["fields"]
    for field_key in phase_fields:
        st_store(user_input[field_key], PHASE_NAME, "user_input", field_key)
    if not No_Submit:
        st.session_state[f"{PHASE_NAME}_ai_response"] = "This phase was skipped."
    st.session_state[f"{PHASE_NAME}_phase_status"] = True
    st.session_state['CURRENT_PHASE'] = min(st.session_state['CURRENT_PHASE'] + 1, len(PHASES) - 1)


def celebration():
    rain(
        emoji="🥳",
        font_size=54,
        falling_speed=5,
        animation_length=1,
    )

# Function to find the image URL
def find_image_url(fields):
    for key, value in fields.items():
        if 'image' in value:
            return value['image']
    return None


def main():
    st.set_page_config(initial_sidebar_state="collapsed")

    st.json(st.session_state)


    if 'TOTAL_PRICE' not in st.session_state:
        st.session_state['TOTAL_PRICE'] = 0

    with st.sidebar:
        selected_llm = st.selectbox("Select Language Model", options=LLM_CONFIGURATIONS.keys(), key="selected_llm")
        # Get the initial LLM configuration from the selected model
        initial_config = LLM_CONFIGURATIONS[selected_llm]

        # Parameter adjustment inputs
        st.session_state['llm_config'] = {
            "model": initial_config["model"],
            "temperature": st.slider("Temperature", min_value=0.0, max_value=1.0,
                                     value=float(initial_config.get("temperature", 1.0)), step=0.01),
            "max_tokens": st.slider("Max Tokens", min_value=50, max_value=4000,
                                    value=int(initial_config.get("max_tokens", 1000)), step=50),
            "top_p": st.slider("Top P", min_value=0.0, max_value=1.0, value=float(initial_config.get("top_p", 1.0)), step=0.1),
            "frequency_penalty": st.slider("Frequency Penalty", min_value=0.0, max_value=1.0,
                                           value=float(initial_config.get("frequency_penalty", 0.0)), step=0.01),
            "presence_penalty": st.slider("Presence Penalty", min_value=0.0, max_value=1.0,
                                          value=float(initial_config.get("presence_penalty", 0.0)), step=0.01),
            "price_input_token_1M": st.number_input("Input Token Price 1M", value=initial_config.get("price_input_token_1M", 0)),
            "price_output_token_1M": st.number_input("Output Token Price 1M", value=initial_config.get("price_output_token_1M", 0))
        }

        if DISPLAY_COST:
            st.write("Price : ${:.6f}".format(st.session_state['TOTAL_PRICE']))

        with st.sidebar:
            st.subheader("Chat History")
            for history in st.session_state['chat_history']:
                st.markdown(f"**User:** {history['user']}")
                st.markdown(f"**AI:** {history['assistant']}")
                st.markdown("---")

    if 'CURRENT_PHASE' not in st.session_state:
        st.session_state['CURRENT_PHASE'] = 0

    st.title(APP_TITLE)
    st.markdown(APP_INTRO)

    if APP_HOW_IT_WORKS:
        with st.expander("Learn how this works", expanded=False):
            st.markdown(APP_HOW_IT_WORKS)

    if SHARED_ASSET:
        with open(SHARED_ASSET["path"], "rb") as asset_file:
            st.download_button(label=SHARED_ASSET["button_text"],
                               data=asset_file,
                               file_name=SHARED_ASSET["name"],
                               mime="application/octet-stream")

    if HTML_BUTTON:
        st.link_button(label=HTML_BUTTON["button_text"], url=HTML_BUTTON["url"])

    i = 0

    while i <= st.session_state['CURRENT_PHASE']:
        submit_button = False
        skip_button = False
        final_phase_name = list(PHASES.keys())[-1]
        final_key = f"{final_phase_name}_ai_response"

        PHASE_NAME = list(PHASES.keys())[i]
        PHASE_DICT = PHASES[PHASE_NAME]
        fields = PHASE_DICT["fields"]

        st.write(f"#### Phase {i + 1}: {PHASE_DICT['name']}")

        build_field(PHASE_NAME, fields)

        key = f"{PHASE_NAME}_phase_status"

        user_prompt_template = PHASE_DICT.get("user_prompt", "")
        if PHASE_DICT.get("show_prompt", False):
            with st.expander("View/edit full prompt"):
                formatted_user_prompt = st.text_area(
                    label="Prompt",
                    height=100,
                    max_chars=50000,
                    value=format_user_prompt(user_prompt_template, user_input, PHASE_NAME),
                    disabled=PHASE_DICT.get("read_only_prompt",False)
                    )
        else:
            formatted_user_prompt = format_user_prompt(user_prompt_template, user_input, PHASE_NAME)

        if PHASE_DICT.get("no_submission", False):
            if key not in st.session_state:
                st.session_state[key] = True
                st.session_state['CURRENT_PHASE'] = min(st.session_state['CURRENT_PHASE'] + 1, len(PHASES) - 1)
                st.session_state[f"{PHASE_NAME}_phase_completed"] = True
                st.rerun()

        if key not in st.session_state:
            st.session_state[key] = False

        if not st.session_state.get(f"{PHASE_NAME}_phase_completed", False):
            with st.container():
                col1, col2 = st.columns(2)
                with col1:
                    submit_button = st.button(label=PHASE_DICT.get("button_label", "Submit"), type="primary",
                                              key=f"submit {i}")
                with col2:
                    if PHASE_DICT.get("allow_skip", False):
                        skip_button = st.button(label="Skip Question", key=f"skip {i}")

        key = f"{PHASE_NAME}_ai_response"
        if key in st.session_state:
            st.info(st.session_state[key], icon="🤖")

        key = f"{PHASE_NAME}_ai_score_debug"
        if key in st.session_state:
            st.info(st.session_state[key], icon="🤖")

        key = f"{PHASE_NAME}_ai_response_revision_1"
        # If there are any revisions, enter the loop
        if key in st.session_state:
            z = 1
            while z <= PHASE_DICT.get("max_revisions",10):
                key = f"{PHASE_NAME}_ai_response_revision_{z}"
                if key in st.session_state:
                    st.info(st.session_state[key], icon="🤖")
                z += 1

        if submit_button:
            for field_key, field in fields.items():
                st_store(user_input[field_key], PHASE_NAME, "user_input", field_key)

            phase_instructions = PHASE_DICT.get("phase_instructions", "")
            user_prompt_template = PHASE_DICT.get("user_prompt", "")

            image_url = find_image_url(PHASE_DICT.get('fields', {}))

            if PHASE_DICT.get("ai_response", True):
                if PHASE_DICT.get("scored_phase", False):
                    if "rubric" in PHASE_DICT:
                        scoring_instructions = build_scoring_instructions(PHASE_DICT["rubric"])
                        ai_feedback = call_openai_completions(phase_instructions, formatted_user_prompt, image_url)
                        st.info(body=ai_feedback, icon="🤖")
                        ai_score = call_openai_completions(scoring_instructions, ai_feedback)
                        st.info(ai_score, icon="🤖")
                        st_store(ai_feedback, PHASE_NAME, "ai_response")
                        st_store(ai_score, PHASE_NAME, "ai_score_debug")
                        score = extract_score(ai_score)
                        st_store(score, PHASE_NAME, "ai_score")
                        st.session_state['chat_history'].append({
                            "user": formatted_user_prompt,
                            "assistant": ai_feedback
                        })
                        st.session_state["ai_score"] = ai_score
                        st.session_state['score'] = score
                        if check_score(PHASE_NAME):
                            st.session_state['CURRENT_PHASE'] = min(st.session_state['CURRENT_PHASE'] + 1, len(PHASES) - 1)
                            st.session_state[f"{PHASE_NAME}_phase_completed"] = True
                            st.rerun()
                        else:
                            st.warning("You haven't passed. Please try again.")
                    else:
                        st.error('You need to include a rubric for a scored phase', icon="🚨")
                else:
                    ai_feedback = call_openai_completions(phase_instructions, formatted_user_prompt, image_url)
                    st_store(ai_feedback, PHASE_NAME, "ai_response")
                    st.session_state['chat_history'].append({
                        "user": formatted_user_prompt,
                        "assistant": ai_feedback
                    })
                    st.session_state['CURRENT_PHASE'] = min(st.session_state['CURRENT_PHASE'] + 1, len(PHASES) - 1)
                    st.session_state[f"{PHASE_NAME}_phase_completed"] = True
                    st.rerun()
            else:
                res_box = st.info(body="", icon="🤖")
                result = ""
                hard_coded_message = PHASE_DICT.get('custom_response', None)
                hard_coded_message = format_user_prompt(hard_coded_message, user_input, PHASE_NAME)
                for char in hard_coded_message:
                    result += char
                    res_box.info(body=result, icon="🤖")
                st.session_state[f"{PHASE_NAME}_ai_response"] = hard_coded_message
                st.session_state['chat_history'].append({
                    "user": formatted_user_prompt,
                    "assistant": hard_coded_message
                })
                st.session_state['CURRENT_PHASE'] = min(st.session_state['CURRENT_PHASE'] + 1, len(PHASES) - 1)
                st.session_state[f"{PHASE_NAME}_phase_completed"] = True
                st.rerun()

        if PHASE_DICT.get("allow_revisions", False):
            if f"{PHASE_NAME}_ai_response" in st.session_state:
                # Check if the current phase is the latest completed phase
                is_latest_completed_phase = i == st.session_state['CURRENT_PHASE'] or (
                            i == st.session_state['CURRENT_PHASE'] - 1 and not st.session_state.get(
                        f"{list(PHASES.keys())[i + 1]}_phase_completed", False))

                # Check if it's not the last phase and the phase wasn't skipped
                is_not_last_phase = PHASE_NAME != final_phase_name
                is_not_skipped = not st.session_state.get(f"{PHASE_NAME}_skipped", False)

                if is_latest_completed_phase and is_not_last_phase and is_not_skipped:
                    with st.expander("Revise this response?"):
                        max_revisions = PHASE_DICT.get("max_revisions", 10)
                        if f"{PHASE_NAME}_revision_count" not in st.session_state:
                            st_store(0, PHASE_NAME, "revision_count")
                        if st.session_state[f"{PHASE_NAME}_revision_count"] < max_revisions:
                            st.session_state['additional_prompt'] = st.text_input("Enter additional prompt", value="",
                                                                                  key=PHASE_NAME)
                            if st.button("Revise", key=f"revise_{i}"):
                                st.session_state[f"{PHASE_NAME}_revision_count"] += 1

                                phase_instructions = PHASE_DICT.get("phase_instructions", "")
                                user_prompt_template = PHASE_DICT.get("user_prompt", "")
                                formatted_user_prompt = format_user_prompt(user_prompt_template, user_input, PHASE_NAME)

                                formatted_user_prompt += st.session_state['additional_prompt']

                                ai_feedback = call_openai_completions(phase_instructions, formatted_user_prompt)

                                st_store(ai_feedback, PHASE_NAME, "ai_response_revision_" + str(
                                    st.session_state[f"{PHASE_NAME}_revision_count"]))
                                st.session_state['chat_history'].append({
                                    "user": formatted_user_prompt,
                                    "assistant": ai_feedback
                                })
                                st.rerun()
                        else:
                            st.warning("Revision limits exceeded")

        if skip_button:
            skip_phase(PHASE_NAME)
            st.session_state[f"{PHASE_NAME}_phase_completed"] = True
            st.session_state[f"{PHASE_NAME}_skipped"] = True
            st.rerun()

        if final_key in st.session_state and i == st.session_state['CURRENT_PHASE']:
            st.success(COMPLETION_MESSAGE)
            if COMPLETION_CELEBRATION:
                celebration()

        i = min(i + 1, len(PHASES))

if __name__ == "__main__":
    main()