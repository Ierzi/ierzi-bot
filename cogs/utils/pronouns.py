import psycopg2
from rich.console import Console
from typing import Literal
from dotenv import load_dotenv
import os
from enum import Enum

# IF YOU WANNA UPDATE PRONOUNS
# UPDATE ALL OF THIS
# - SUPPORTED_PRONOUNS
# - pronouns_data
# (__main__.py) (pronouns_set()) set_pronouns_embed.description
# (__main__.py) (pronouns_set()) pronouns_option
# (__main__.py) (pronouns_set()) pronouns_select_callback()

# --------------

# -- Types

# only have the most common pronouns yet
#TODO: add more pronouns
SUPPORTED_PRONOUNS = Literal['he/him', 'she/her', 'they/them/themselves', 'they/them/themself', 'any'] # any will probably use they/them
pronoun = str #he
pronouns = str #he/him
_pronouns_data = tuple[pronoun, pronoun, pronoun, pronoun, pronoun]
_returned_pronouns_data = _pronouns_data | pronoun

class PronounEnum(Enum):
    SUBJECT = 1
    OBJECT = 2
    POSSESSIVE = 3
    POSSESSIVE_2 = 4
    REFLEXIVE = 5
    ALL = 6

ALL = PronounEnum.ALL

pronouns_data: dict[str, _pronouns_data] = {
    'he/him': ('he', 'him', 'his', 'his', 'himself'),
    'she/her': ('she', 'her', 'her', 'hers', 'herself'),
    'they/them/themselves': ('they', 'them', 'their', 'theirs', 'themselves'),
    'they/them/themself': ('they', 'them', 'their', 'theirs', 'themself'),
    'any': ('they', 'them', 'their', 'theirs', 'themselves') # Like I said on SUPPORTED_PRONOUNS
}


console = Console()

load_dotenv()
conn = psycopg2.connect(
    host=os.getenv("PGHOST"),
    database=os.getenv("PGDATABASE"),
    user=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD"),
    port=os.getenv("PGPORT")
)
cur = conn.cursor()

async def set_pronouns(
        user_id: int, 
        pronouns: SUPPORTED_PRONOUNS
    ) -> None:
    
    cur.execute("""
                INSERT INTO users (user_id, pronouns) 
                VALUES (%s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET pronouns = EXCLUDED.pronouns;
                """, (user_id, pronouns))
    conn.commit()

    console.print(f"Set {user_id}'s pronouns to {pronouns}.")

async def get_pronouns(
        user_id: int,
        get_na: bool = False
    ) -> pronouns:
    
    cur.execute("SELECT pronouns FROM users WHERE user_id = %s", (user_id,))
    row = cur.fetchone()

    if row and row[0]:
        return row[0]
    else: 
        return 'na' if get_na else 'they/them/themselves'
    
async def get_pronoun(
        user_id: int,
        data_returned: PronounEnum = ALL
    ) -> _returned_pronouns_data:
    
    cur.execute("SELECT pronouns FROM users WHERE user_id = %s", (user_id,))
    row = cur.fetchone()

    if row and row[0]:
        _pronouns: pronouns = row[0]
        
        match data_returned:
            case PronounEnum.SUBJECT:
                return pronouns_data[_pronouns][0]
            case PronounEnum.OBJECT:
                return pronouns_data[_pronouns][1]
            case PronounEnum.POSSESSIVE:
                return pronouns_data[_pronouns][2]
            case PronounEnum.POSSESSIVE_2:
                return pronouns_data[_pronouns][3]
            case PronounEnum.REFLEXIVE:
                return pronouns_data[_pronouns][4]
            case PronounEnum.ALL:
                return pronouns_data[_pronouns]
    else:
        # they/them/themselves
        match data_returned:
            case PronounEnum.SUBJECT:
                return pronouns_data['they/them/themselves'][0]
            case PronounEnum.OBJECT:
                return pronouns_data['they/them/themselves'][1]
            case PronounEnum.POSSESSIVE:
                return pronouns_data['they/them/themselves'][2]
            case PronounEnum.POSSESSIVE_2:
                return pronouns_data['they/them/themselves'][3]
            case PronounEnum.REFLEXIVE:
                return pronouns_data['they/them/themselves'][4]
            case PronounEnum.ALL:
                return pronouns_data['they/them/themselves']
        
