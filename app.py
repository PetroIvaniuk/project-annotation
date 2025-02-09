import streamlit as st
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from streamlit_gsheets import GSheetsConnection

import pandas as pd
from difflib import SequenceMatcher

from utils import generate_original_corrected_texts


# Set Streamlit page configuration
st.set_page_config(layout="wide")

# Load the configuration settings from the config_auth.yaml file
with open('config_auth.yaml') as f:
	config_auth = yaml.load(f, Loader=SafeLoader)

# Set up the authenticator for the Streamlit application
authenticator = stauth.Authenticate(
	config_auth['credentials'],
	config_auth['cookie']['name'],
	config_auth['cookie']['key'],
	config_auth['cookie']['expiry_days'],
)

# Creating a login widget
try:
	authenticator.login()
except stauth.LoginError as e:
	st.error(e)


if st.session_state["authentication_status"]:
	authenticator.logout()

	with open('text_intro.txt', 'r') as f:
		text_intro = f.read()

	def on_click_a():
		results_list = []
		for k, v in st.session_state.items():
			if 'feedback' in k:
				item_feedback = {
					'idx': k.split('_')[-1],
					'feedback': v,
					'author': st.session_state['name']
				}
				results_list.append(item_feedback)
		st.session_state.df_results = pd.DataFrame(results_list)

		if st.session_state.df_results[st.session_state.df_results['feedback'].isna()].shape[0]==0:
			# clear cache before write data to spreadshit
			st.cache_data.clear()
			# open already annotated data
			conn_data_write = st.connection('gsheets_out', type=GSheetsConnection)
			df_data_write = conn_data_write.read()
			# connect opened data with annotated data during one session
			df_data_write_upd = pd.concat([df_data_write, st.session_state.df_results], axis=0)
			# update annotated data
			conn_data_write.update(
				data=df_data_write_upd,
			)
			# change button status
			st.cache_data.clear()
			st.session_state.button_1_clicked = True

	def on_click_b():
		st.session_state.button_1_clicked = False

	if 'button_1_clicked' not in st.session_state:
		st.session_state.button_1_clicked = False

	_, col01, _ = st.columns((0.5, 2, 0.5))
	with col01:
		st.write(f'Welcome *{st.session_state["name"]}*')

		with st.container(border=True):
			st.markdown(text_intro)
			# st.write(st.session_state)

		if not st.session_state.button_1_clicked:
			conn_data = st.connection("gsheets_in", type=GSheetsConnection)
			conn_feedback = st.connection("gsheets_out", type=GSheetsConnection)

			df_feedback = conn_feedback.read()
			feedback_ids = df_feedback['idx'].unique().tolist()

			df_data = conn_data.read()
			st.session_state.num_examples = df_data.shape[0] - len(feedback_ids)
			df_data = df_data[~df_data['idx'].isin(feedback_ids)].sample(3, random_state=42).reset_index().copy()
			# st.write(df_data)

			for i, row in df_data.iterrows():
				with st.container(border=True):
					original, corrected = generate_original_corrected_texts(row['text'], row['correction'])
					st.write(original)
					st.divider()
					st.write(corrected)

				sentiment_mapping = ["one", "two", "three", "four", "five"]
				selected = st.feedback("faces", key=f'feedback_{int(row["idx"])}', disabled=False)
				st.write('')

				if selected is not None:
					st.markdown(f"You selected {sentiment_mapping[selected]} star(s).")

			if st.button("Надіслати результати", key='but_a', on_click=on_click_a):
				num_unlabeled = st.session_state.df_results[st.session_state.df_results['feedback'].isna()].shape[0]
				if num_unlabeled!=0:
					st.warning(f"You missed {num_unlabeled} examples. Please annotate!")

		if st.session_state.button_1_clicked:
			st.info(f"Дякуємо за Вашу допомогу та внесок y проект!\n\
				Для успішного завершення проекту залишилось проанотувати ще {st.session_state.num_examples} прикладів.\n\
				Якщо маєте хороший настрій та достатньо сили, то проанотуйте ще 10 нових прикладів!"
				)
			st.button("Завантажити нові дані для анаотації", key='but_b', on_click=on_click_b)

elif st.session_state["authentication_status"] is None:
	st.warning('Please enter your username and password')

elif st.session_state["authenticaion_status"] is False:
	st.error('Username/password is incorrect')