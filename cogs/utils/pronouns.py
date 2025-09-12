import psycopg2
from rich.console import Console
from typing import Literal
from dotenv import load_dotenv
import os
from enum import Enum

# -- Types

# only have the most common pronouns yet
#TODO: add more pronouns
SUPPORTED_PRONOUNS = Literal['he/him', 'she/her', 'they/them', 'any'] # any will probably use they/them
type pronoun = str
type pronouns = str
type _pronouns_data = tuple[pronoun, pronoun, pronoun, pronoun, pronoun]
type _returned_pronouns_data = _pronouns_data | pronoun

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
    'they/them': ('they', 'them', 'their', 'theirs', 'themselves'),
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

# Adding the columns
cur.execute("""
            ALTER TABLE users
            ADD COLUMN pronouns TEXT;
            """)

conn.commit()

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

async def get_pronouns(
        user_id: int
    ) -> pronouns:
    
    cur.execute("SELECT pronouns FROM users WHERE user_id = %s", (user_id,))
    row = cur.fetchone()

    if row and row[0]:
        return row[0]
    else: 
        return 'they/them'
    
async def get_pronoun(
        user_id: int,
        data_returned: PronounEnum = ALL
    ) -> _returned_pronouns_data:
    
    cur.execute("SELECT pronouns FROM users WHERE user_id = %s", (user_id,))
    row = cur.fetchone()

    if row and row[0]:
        _pronouns: pronouns = row[0]
        if _pronouns not in SUPPORTED_PRONOUNS:
            console.print('invalid pronouns')
            return 
        
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
        # they/them
        match data_returned:
            case PronounEnum.SUBJECT:
                return pronouns_data['they/them'][0]
            case PronounEnum.OBJECT:
                return pronouns_data['they/them'][1]
            case PronounEnum.POSSESSIVE:
                return pronouns_data['they/them'][2]
            case PronounEnum.POSSESSIVE_2:
                return pronouns_data['they/them'][3]
            case PronounEnum.REFLEXIVE:
                return pronouns_data['they/them'][4]
            case PronounEnum.ALL:
                return pronouns_data['they/them']
        
