from dataclasses import dataclass
import streamlit as st
import pandas as pd
import numpy as np

x = """
Features:
- Initiative Tracker, which allows players to add their name and initiative
  - highlights active row, or rotates the list as the round goes on
  - could display extra data, like AC or HP
- Graphs showing damage over time (burn down), could say who's expected to win at the moment

To do:
- auto-clear form field, only add new data when both fields are present
- allow edit/ update/ delete

New idea:
Add Sidebar for initiative tracker, main page for character stats/ character card.


0. Auto-clear form input, only add new character when both fields are present
0.5. Update/ Delete character
1. Track current turn (highlight row, or always make it the top)
1.25. Track rounds/ who's gone in the round, etc. (order by who's gone, then by initiative)
1.5. Make inititive table pretty
2. HP management
3. AC management
4. HP Burndown for each character
5. Predicted victory based on burndown rates
6. Predicted number of rounds left
7. Graph the burndown with victory and remaining rounds
8. Add Character Cards
9. Initiative on sidebar
10. Shared state across users
11. Scrape character info from character sheets (what about monsters or NPCs?) (from dndbeyond, or could download everyone's character sheets)

* reaction tracker per round
* status tracking?  concentration tracker?
* add HP bar - track max vs current, could have extra HP (temp?)
* Add other ability scores
* input validation
* write character cards in columns
* temp hp / enforce maximum
"""

# TODO: add minimum values here, instead of when writing data
@dataclass
class Character:
    name: str
    initiative: int
    hp: int = 0
    ac: int = 0
    max_hp: int = 1


def load_characters():
    return {
        'Takan': Character('Takan', 18, 26, 19, 59),
        'Kasjin': Character('Kasjin', 6, 51, 19, 51),
        'Aby the Aboleth': Character('Aby the Aboleth', 24, 15, 16, 135)
    }

def initialize():
    if 'characters' not in st.session_state:
        st.session_state ['characters'] = load_characters()

    if 'turn' not in st.session_state:
        st.session_state['turn'] = 1

    if 'round' not in st.session_state:
        st.session_state['round'] = 1


st.markdown(
    """
    <style>
        .stProgress > div > div > div > div {
            background-image: linear-gradient(to left, #C10505, green, forestgreen);
        }
    </style>""",
    unsafe_allow_html=True,
)

def render_char_card(character, parent=st):
    parent.subheader(character.name)
    health_percent = character.hp / character.max_hp
    col1, col2 = parent.columns(2)
    hp = '☠️' if character.hp == 0 else '{0} / {1}'.format(character.hp, character.max_hp)
    col1.metric(label='❤️ HP', value=hp)
    col1.progress(health_percent)
    col2.metric(label='🛡️ AC', value=character.ac)


initialize()

characters = st.session_state.characters

with st.form("new_character", clear_on_submit=True):
    name_col, init_col, hp_col, ac_col, submit_col = st.columns(5)
    name_col.text_input("Character", key="name")
    init_col.text_input("Initiative", key="initiative")
    hp_col.text_input("HP", key="hp")
    ac_col.text_input("AC", key="ac")
    if submit_col.form_submit_button("Add"):
        characters[st.session_state.name] = Character(
                name=st.session_state.name, 
                initiative=int(st.session_state.initiative),
                ac=int(st.session_state.ac),
                hp=int(st.session_state.hp),
                max_hp=int(st.session_state.hp)
            )


with st.form("damage", clear_on_submit=True):
    char_col, amount_col, type_col = st.columns([2, 1, 1])
    amount = amount_col.number_input('', step=1, min_value=0)
    type = type_col.radio('', ['Damage', 'Heal', 'Total'])
    name = char_col.selectbox('', ['--'] + list(characters.keys()))
    # Every form must have a submit button.
    submitted = st.form_submit_button("Ka-pow!")
    if submitted:
        if name != '--':
            char = characters[name]
            if type == 'Total':
                char.hp = amount
            else:
                multiplier = -1 if type == 'Damage' else 1
                char.hp = max(char.hp + amount * multiplier, 0)


# TODO: sidebar should show if there are no characters yet, with empty df.
if len(characters) != 0:
    st.sidebar.caption("Round {0} - turn {1}".format(st.session_state.round, st.session_state.turn))
    characters_list = list(characters.values())
    characters_list.sort(key=lambda char: char.initiative, reverse=True)
    cols = st.columns(2)
    i = 0
    for character in characters_list:
        col = cols[i % 2]
        render_char_card(character, col)
        col.title('')
        i += 1
    df = pd.DataFrame(characters_list)[['name', 'initiative']]
    # df.set_index('name', inplace=True) ## This sets name as the index, which removes the index column.
    st.sidebar.title('Current Turn: {0}'.format(characters_list[st.session_state.turn - 1].name))
    st.sidebar.caption('On Deck: {0}'.format(characters_list[st.session_state.turn % len(characters_list)].name))
    st.sidebar.header('Turn Order')
    st.sidebar.write(
            df.style.apply(lambda x: ['background-color: grey' 
                                  if (x.name == st.session_state.turn - 1)
                                  else '' for i in x], axis=1)
    )
    button = st.sidebar.button('Next Turn')
    if button:
        if st.session_state.turn == len(characters):
            st.session_state.round += 1
            st.session_state.turn = 1
        else:
            st.session_state.turn = st.session_state.turn + 1
        st.experimental_rerun() # forces a rerun, or else the turn counter renders behind a turn.

    st.sidebar.title('')
    st.sidebar.title('')

    with st.sidebar.form("remove", clear_on_submit=True):
        name = st.selectbox("Character", ['--'] + list(characters.keys()))
        if st.form_submit_button("Remove Character"):
            if name != '--':
                del characters[name]
                st.experimental_rerun() # forces a rerun, so other components have the right characters

else:
    st.sidebar.caption("Add characters to view turn order.")