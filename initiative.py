from dataclasses import dataclass
import streamlit as st
import pandas as pd
import numpy as np

x = """
Done:
+ auto-clear form fields
+ move init tracker to sidebar
+ add character cards
+ Track current turn (highlight row, or always make it the top)
+ Track rounds/ who's gone in the round, etc. (order by who's gone, then by initiative)
+ Make inititive table pretty
+ HP management
+ Add Character Cards
+ Initiative on sidebar
+ write character cards in columns
+ add HP bar - track max vs current, could have extra HP (temp?)
+ HP and AC tracker
+ highlight active turn
+ health percent can't be greater than 100% (enforce max health)
+ config file (dark theme)
+ tab header
+ reorg/ clean code


To do:
- PC data
- handle null/ empty inputs
- move character data validations to dataclass (min/ max hp)
- Allow updates to a character by adding them again
- Don't use state when you don't need to
- Add "combat" object to contain turn/round count and initiative order.


Feature ideas:
- better "edit"/ "update" options?
- AC management
- HP Burndown for each character
- Predicted victory based on burndown rates
- Predicted number of rounds left
- Graph the burndown with victory and remaining rounds
- Shared state across users
- Scrape character info from character sheets (what about monsters or NPCs?) (from dndbeyond, or could download everyone's character sheets)
- reaction tracker per round
- status tracking?  concentration tracker?
- Add other ability scores
- temp hp


Questions:
* what happens when form fields are empty and it's submitted?
"""

ss = st.session_state

def build():
    set_styles()
    initialize()

    new_character_form()
    damage_form()

    characters_list = list(ss.characters.values())
    characters_list.sort(key=lambda char: char.initiative, reverse=True)
    render_initiative_board(characters_list)
    render_character_cards(characters_list)


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


def set_styles():
    st.set_page_config(page_title="Initiative Tracker", page_icon="🐉")
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


def render_initiative_board(characters_list, parent=st.sidebar):
    if len(characters_list) == 0:
        return parent.caption("Add characters to view turn order.")
    parent.caption("Round {0} - turn {1}".format(ss.round, ss.turn))
    parent.title('Current Turn: {0}'.format(characters_list[ss.turn - 1].name))
    parent.caption('On Deck: {0}'.format(characters_list[ss.turn % len(characters_list)].name))
    parent.header('Turn Order')
    df = pd.DataFrame(characters_list)[['name', 'initiative']]
    # df.set_index('name', inplace=True) ## This sets name as the index, which removes the index column.
    parent.write(
            df.style.apply(lambda x: ['background-color: grey' 
                                  if (x.name == ss.turn - 1)
                                  else '' for i in x], axis=1)
    )
    if parent.button('Next Turn'):
        if ss.turn == len(ss.characters):
            ss.round += 1
            ss.turn = 1
        else:
            ss.turn = ss.turn + 1
        st.experimental_rerun() # forces a rerun, or else the turn counter renders behind a turn.
    parent.title('')
    parent.title('')
    with parent.form("remove", clear_on_submit=True):
        name = st.selectbox("Character", ['--'] + list(ss.characters.keys()))
        if st.form_submit_button("Remove Character"):
            if name != '--':
                del ss.characters[name]
                st.experimental_rerun() # forces a rerun, so other components have the right characters


def render_character_cards(characters_list):
    if len(characters_list) == 0: return
    cols = st.columns(2)
    i = 0
    for character in characters_list:
        col = cols[i % 2]
        render_char_card(character, col)
        col.title('')
        i += 1


def new_character_form():
    with st.form("new_character", clear_on_submit=True):
        name_col, init_col, hp_col, ac_col, submit_col = st.columns(5)
        name = name_col.text_input("Character", key="name")
        init = init_col.number_input("Initiative", key="initiative", min_value=0)
        hp = hp_col.number_input("HP", key="hp", min_value=0, step=1)
        ac = ac_col.number_input("AC", key="ac", min_value=0, step=1)
        if submit_col.form_submit_button("Add"):
            ss.characters[name] = Character(
                    name=name,
                    initiative=init,
                    ac=ac,
                    hp=hp,
                    max_hp=hp
                )


def damage_form():
    with st.form("damage", clear_on_submit=True):
        char_col, amount_col, type_col = st.columns([2, 1, 1])
        amount = amount_col.number_input('', step=1, min_value=0)
        type = type_col.radio('', ['Damage', 'Heal', 'Total'])
        name = char_col.selectbox('', ['--'] + list(ss.characters.keys()))
        submitted = st.form_submit_button("Ka-pow!")
        if submitted:
            if name != '--':
                char = ss.characters[name]
                # TODO: setting logic in dataclass.  Also min/max when setting Total
                if type == 'Total':
                    char.hp = amount
                elif type == 'Damage':
                    char.hp = max(char.hp - amount, 0)
                elif type == 'Heal':
                    char.hp = min(char.hp + amount, char.max_hp)


build()