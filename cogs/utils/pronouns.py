from rich.console import Console
from typing import Literal
from dotenv import load_dotenv
import os
from enum import Enum
from .database import db

# IF YOU WANNA UPDATE PRONOUNS
# UPDATE ALL OF THIS
# - SUPPORTED_PRONOUNS
# - pronouns_data
# [If pronouns are not hidden]
# - (__main__.py) (pronouns_set()) set_pronouns_embed.description
# - (__main__.py) (pronouns_set()) pronouns_option
# - (__main__.py) (pronouns_set()) pronouns_select_callback()

# --------------

# -- Types

# only have the most common pronouns yet
#TODO: add more pronouns (nameself, neopronouns...) https://en.pronouns.page/pronouns

all_pronouns = [
    "he/him", "she/her", "they/them/themselves", "they/them/themself", "it/its", "one/one's", "any"
] # Not including hidden pronouns
all_pronouns_hidden = all_pronouns.copy().extend(
    [
        "fag/got",
        "nyeh/heh/heh"
    ]
)

SUPPORTED_PRONOUNS = Literal[
    'he/him', 
    'she/her', 
    'they/them/themselves', 
    'they/them/themself', 
    'it/its', 
    "one/one's",
    'any', # any will probably use they/them

    # HIDDEN PRONOUNS
    'fag/got',
    'nyeh/heh/heh'
] 
pronoun = str #e.g. he
pronouns = str #e.g. he/him
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
    'it/its': ('it', 'it', 'its', 'its', 'itself'),
    "one/one's": ("one", "one", "one's", "one's", "oneself"),
    'any': ('they', 'them', 'their', 'theirs', 'themselves'), # Like I said on SUPPORTED_PRONOUNS
    # HIDDEN PRONOUNS
    'fag/got': ('fag', 'got', 'fager', 'fagers', 'fagself'),
    'nyeh/heh/heh': ('nyeh', 'heh', 'heh', 'heh', 'hehself')
}

console = Console()

load_dotenv()

async def set_pronouns(
        user_id: int, 
        pronouns: SUPPORTED_PRONOUNS
    ) -> None:
    
    await db.execute(
        """
        INSERT INTO users (user_id, pronouns) 
        VALUES ($1, $2)
        ON CONFLICT (user_id)
        DO UPDATE SET pronouns = EXCLUDED.pronouns;
        """,
        user_id,
        pronouns,
    )

    console.print(f"Set {user_id}'s pronouns to {pronouns}.")

async def get_pronouns(
        user_id: int,
        get_na: bool = False
    ) -> pronouns:
    
    row = await db.fetchrow("SELECT pronouns FROM users WHERE user_id = $1", user_id)

    if row and row["pronouns"]:
        return row["pronouns"]
    else: 
        return 'na' if get_na else 'they/them/themselves'
    
async def get_pronoun(
        user_id: int,
        data_returned: PronounEnum = ALL
    ) -> _returned_pronouns_data:
    
    row = await db.fetchrow("SELECT pronouns FROM users WHERE user_id = $1", user_id)

    if row and row["pronouns"]:
        _pronouns: pronouns = row["pronouns"]
        
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
        
