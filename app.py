import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from streamlit_gsheets import GSheetsConnection

import datetime
import pandas as pd
from utils import generate_original_corrected_texts


# Set Streamlit page configuration
st.set_page_config(page_title="🇺🇦Grammaticks", layout="wide")

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
	st.write(f'Привіт **{st.session_state["name"]}**')
	authenticator.logout()

	n_samples = 10

	tab1, tab2 = st.tabs(["Annotation", "Leaderboard"])

	with open('text_intro.txt', 'r') as f:
		text_intro = f.read()

	def on_click_a():
		results_list = []
		for k, v in st.session_state.items():
			if 'feedback' in k:
				feedback_idx = k.split('_')[-1]
				item_feedback = {
					'idx': feedback_idx,
					'feedback': v,
					'is_shit': st.session_state[f'checkbox_{feedback_idx}'],
					'author': st.session_state['name']
				}
				results_list.append(item_feedback)
		st.session_state.df_results = pd.DataFrame(results_list)
		st.session_state.df_results['time'] = datetime.datetime.now()

		if st.session_state.df_results[st.session_state.df_results['feedback'].isna()].shape[0]==0:
			# clear cache before write data to spreadsheet
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

	with tab1:
		_, col_01, _ = st.columns((0.5, 2, 0.5))
		with col_01:
			with st.container(border=True):
				st.markdown(text_intro)
				# st.write(st.session_state)

			if not st.session_state.button_1_clicked:
				conn_data = st.connection("gsheets_in", type=GSheetsConnection)
				conn_feedback = st.connection("gsheets_out", type=GSheetsConnection)

				st.session_state.df_annotation = conn_feedback.read()
				feedback_ids = st.session_state.df_annotation['idx'].unique().tolist()

				df_data = conn_data.read()
				st.session_state.num_examples = df_data.shape[0] - len(feedback_ids)
				df = df_data[~df_data['idx'].isin(feedback_ids)].sample(
					n_samples, random_state=st.session_state.num_examples
				).reset_index().copy()

				st.write('')
				st.write('')
				for i, row in df.iterrows():
					with st.container(border=True):
						original, corrected = generate_original_corrected_texts(row['text'], row['correction'])
						st.write(original)
						st.divider()
						st.write(corrected)

					# add feedback faces
					sentiment_mapping = ["one", "two", "three", "four", "five"]
					selected = st.feedback("faces", key=f'feedback_{int(row["idx"])}', disabled=False)

					# add quality text checkbox
					selected_checkbox = st.checkbox(
						"Складно оцінити якість виправлення.",
						key=f'checkbox_{int(row["idx"])}'
					)
					st.write('')

					if selected is not None:
						st.markdown(f"You selected {sentiment_mapping[selected]} star(s).")

				if st.button("Надіслати результати", key='but_a', on_click=on_click_a):
					num_unlabeled = st.session_state.df_results[st.session_state.df_results['feedback'].isna()].shape[0]
					if num_unlabeled!=0:
						st.warning(f"You have missed {num_unlabeled} example(s). Please annotate!")

			if st.session_state.button_1_clicked:
				st.info(f"Дякуємо за вашу допомогу та внесок y проєкт! Якщо маєте гарний настрій, проанотуйте ще\
				10 прикладів, будь ласка! Кількість прикладів до успішного завершення проєкту: {st.session_state.num_examples}.")
				st.button("Продовжити", key='but_b', on_click=on_click_b)

	with tab2:
		df_annotation_all = st.session_state.df_annotation.copy()
		df_annotation_all['point'] = df_annotation_all['feedback']+1
		df_leader = df_annotation_all.groupby(['author']).agg(
			avg_point=('point', 'mean'),
			number=('point', 'count')
		).reset_index()
		df_leader['avg_point'] = df_leader['avg_point'].round(2)
		df_leader['rank'] = df_leader['number'].rank(method='min', ascending=False)

		_, col2, _ = st.columns((2, 2, 2))
		with col2:
			st.markdown('## Leaderboard - Top 5')
			st.dataframe(df_leader.sort_values('rank').head(5), use_container_width=True, hide_index=True)

elif st.session_state["authentication_status"] is None:
	st.warning('Please enter your username and password')

elif st.session_state["authenticaion_status"] is False:
	st.error('Username/password is incorrect')