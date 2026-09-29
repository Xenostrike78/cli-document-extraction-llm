# identity/indian_names_kb.py
# Lookup tables for common Indian name variants.
#
# Two exports:
#   NAME_VARIANT_KB  - full structured list used by name_rag.py for TF-IDF indexing
#   FLAT_ALIASES     - flat dict built from the KB, used by name_matcher.py for O(1) lookups
#
# To add a new name group, append an entry to NAME_VARIANT_KB.
# FLAT_ALIASES is generated automatically at the bottom of this file.

from typing import TypedDict, List


class NameVariantGroup(TypedDict):
    canonical: str
    variants: List[str]
    religion: str
    region: str
    notes: str


NAME_VARIANT_KB: List[NameVariantGroup] = [

    # ─────────────────────────────────────────────
    # MUSLIM NAMES
    # ─────────────────────────────────────────────
    {
        "canonical": "mohammad",
        "variants": ["mohammed", "muhammad", "mohd", "md", "mohamad", "mehmet",
                     "muhamad", "mahammad", "mohammod", "muhammed", "mahomed",
                     "mahomet", "mohhammad", "mohmmad", "mohomad", "mhd"],
        "religion": "Muslim",
        "region": "pan-India",
        "notes": "Most common Muslim first name; extreme spelling variation in Indian documents."
    },
    {
        "canonical": "abdul",
        "variants": ["abd", "abdu", "abdl", "abdel", "abul", "abool", "abdool",
                     "abd.", "ab."],
        "religion": "Muslim",
        "region": "pan-India",
        "notes": "Prefix meaning 'servant of'; often abbreviated to Abd. or Ab. in marksheets."
    },
    {
        "canonical": "mohammed ali",
        "variants": ["md ali", "mohd ali", "muhammad ali", "mohamad ali"],
        "religion": "Muslim",
        "region": "pan-India",
        "notes": "Compound; handled as phrase variant."
    },
    {
        "canonical": "sheikh",
        "variants": ["shaikh", "shaykh", "shekh", "shiekh", "sheik", "sk"],
        "religion": "Muslim",
        "region": "pan-India",
        "notes": "Surname/title; 'sk' abbreviation common in Bengali documents."
    },
    {
        "canonical": "syed",
        "variants": ["sayyid", "sayyad", "sayyed", "saiyed", "sayed", "saiyad",
                     "seyed", "syyed", "s.", "sy"],
        "religion": "Muslim",
        "region": "pan-India",
        "notes": "Honorific prefix indicating descent from the Prophet."
    },
    {
        "canonical": "khwaja",
        "variants": ["khwja", "khaja", "khawaja", "kwaja", "khuja"],
        "religion": "Muslim",
        "region": "North India",
        "notes": "Title used by Sufi lineages."
    },
    {
        "canonical": "hussain",
        "variants": ["husain", "husein", "hussein", "hossain", "hossein",
                     "hosain", "hosein"],
        "religion": "Muslim",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "ali",
        "variants": ["alee", "aly", "alii"],
        "religion": "Muslim",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "khan",
        "variants": ["khaan", "khn"],
        "religion": "Muslim",
        "region": "North India",
        "notes": "Surname; rarely abbreviated but OCR errors common."
    },
    {
        "canonical": "ansari",
        "variants": ["ansary", "ansaree", "ansaari"],
        "religion": "Muslim",
        "region": "North/East India",
        "notes": ""
    },
    {
        "canonical": "qureshi",
        "variants": ["quereshi", "quraishi", "quraishi", "qurashi", "kureshi",
                     "qurayshi", "quraishy"],
        "religion": "Muslim",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "rahaman",
        "variants": ["rahman", "rehman", "rahamaan", "rehaman", "rahiman"],
        "religion": "Muslim",
        "region": "East/North India",
        "notes": "Standalone name or part of compound (Abdur Rahman)."
    },
    {
        "canonical": "pathan",
        "variants": ["patan", "pathaan", "paathan"],
        "religion": "Muslim",
        "region": "North/West India",
        "notes": ""
    },
    {
        "canonical": "mirza",
        "variants": ["mirzaa", "mirja", "mirjaa"],
        "religion": "Muslim",
        "region": "North India",
        "notes": ""
    },
    {
        "canonical": "begum",
        "variants": ["begam", "bigum", "bgum", "bg."],
        "religion": "Muslim",
        "region": "pan-India",
        "notes": "Female honorific."
    },
    {
        "canonical": "fatima",
        "variants": ["fathima", "fatema", "fateema", "fatimah", "fatma",
                     "phatima", "phathima"],
        "religion": "Muslim",
        "region": "pan-India",
        "notes": "Common OCR confusion between f and ph in South Indian documents."
    },
    {
        "canonical": "aisha",
        "variants": ["ayesha", "ayisha", "aiesha", "aaisha", "aaiesha"],
        "religion": "Muslim",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "hasan",
        "variants": ["hassan", "hasaan", "haasan", "hssen"],
        "religion": "Muslim",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "ibrahim",
        "variants": ["ibraahim", "ebrahim", "ibraheem", "ibrahim", "ibrahm"],
        "religion": "Muslim",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "ismail",
        "variants": ["esmail", "ismaeel", "ismael", "ysmail"],
        "religion": "Muslim",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "noor",
        "variants": ["nur", "nour", "noore"],
        "religion": "Muslim",
        "region": "pan-India",
        "notes": "Means 'light'; used for both male and female."
    },

    # ─────────────────────────────────────────────
    # HINDU NAMES
    # ─────────────────────────────────────────────
    {
        "canonical": "ram",
        "variants": ["rama", "raam", "raama", "ramu"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": "Divine name; extremely common standalone or as suffix."
    },
    {
        "canonical": "krishna",
        "variants": ["krishan", "kishan", "kishen", "krishen", "kanhaiya",
                     "kanha", "kanhiya", "kaniya"],
        "religion": "Hindu",
        "region": "North India",
        "notes": "Nicknames Kanhaiya/Kanha are informal equivalents used in rural areas."
    },
    {
        "canonical": "rajesh",
        "variants": ["raju", "raja", "raj", "rajesh", "rajeys"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": "Raju/Raja are extremely common hypocoristics for Rajesh."
    },
    {
        "canonical": "suresh",
        "variants": ["sures", "suresh", "sureshu", "suri"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "ramesh",
        "variants": ["rames", "ramesha", "ramu"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "mahesh",
        "variants": ["mahes", "mahesha", "maheshu"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "ganesh",
        "variants": ["ganesha", "ganesh", "ganeshu", "ganu"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "dinesh",
        "variants": ["dines", "dinesha", "dinu"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "naresh",
        "variants": ["nares", "naresha"],
        "religion": "Hindu",
        "region": "North India",
        "notes": ""
    },
    {
        "canonical": "anil",
        "variants": ["aneel", "aniel", "anill"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "sanjay",
        "variants": ["sanjai", "sanjey", "sanje"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "vijay",
        "variants": ["vijay", "vyjay", "vijay", "vyjai", "vijai"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "ajay",
        "variants": ["ajai", "ajey", "ajei"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "rohit",
        "variants": ["rohith", "rohyt", "roheat"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": "South Indian spellings add trailing 'h'."
    },
    {
        "canonical": "amit",
        "variants": ["ameet", "amith", "amitt"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "ankit",
        "variants": ["ankeet", "ankith", "ankyt"],
        "religion": "Hindu",
        "region": "North India",
        "notes": ""
    },
    {
        "canonical": "priya",
        "variants": ["preya", "preeya", "priyaa"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": "Common female name."
    },
    {
        "canonical": "pooja",
        "variants": ["puja", "pooja", "poooja", "pujaa"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": "Ritual name; extremely common female name."
    },
    {
        "canonical": "kavita",
        "variants": ["kavitha", "kawita", "cavita"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "geeta",
        "variants": ["gita", "getha", "geetha", "geata"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "sunita",
        "variants": ["sunitha", "suneeta", "suneta"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "neha",
        "variants": ["neeha", "nehaa", "niha"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "deepak",
        "variants": ["dipak", "depack", "deepack", "dypak"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "vikram",
        "variants": ["vikaram", "vikrum", "bikram"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "lalit",
        "variants": ["laleet", "lalith", "llait"],
        "religion": "Hindu",
        "region": "North India",
        "notes": ""
    },
    {
        "canonical": "rakesh",
        "variants": ["raakesh", "rakesh", "rakes"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "lokesh",
        "variants": ["lokesh", "lokes", "lukesh"],
        "religion": "Hindu",
        "region": "South/North India",
        "notes": ""
    },
    {
        "canonical": "umesh",
        "variants": ["umes", "umesha", "omesh"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "bablu",
        "variants": ["babloo", "bablu", "bablo"],
        "religion": "Hindu",
        "region": "North/East India",
        "notes": "Informal nickname; often the only name used in rural UP/Bihar documents."
    },
    {
        "canonical": "munna",
        "variants": ["munnaa", "muna", "moona"],
        "religion": "Hindu",
        "region": "North India",
        "notes": "Informal nickname for young males."
    },
    {
        "canonical": "guddu",
        "variants": ["gudoo", "gudu", "goodoo"],
        "religion": "Hindu",
        "region": "North India",
        "notes": "Informal nickname."
    },
    {
        "canonical": "pintu",
        "variants": ["pintoo", "pinto", "pintu"],
        "religion": "Hindu",
        "region": "North India",
        "notes": "Informal nickname common in UP/Bihar."
    },
    {
        "canonical": "rinku",
        "variants": ["rinkoo", "rynku", "rinku"],
        "religion": "Hindu",
        "region": "North India",
        "notes": "Informal nickname (male/female)."
    },
    {
        "canonical": "sonu",
        "variants": ["sonoo", "sonnu", "soonu"],
        "religion": "Hindu",
        "region": "North India",
        "notes": "Informal nickname (male/female)."
    },
    {
        "canonical": "ravi",
        "variants": ["raavi", "rabi", "ravy"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "shiv",
        "variants": ["shiva", "siva", "siwa", "shiv"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "om",
        "variants": ["aum", "ohm"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": "Sacred syllable used as a name prefix."
    },
    {
        "canonical": "laxmi",
        "variants": ["lakshmi", "laksmi", "luxmi", "lakxmi"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": "Spelling varies wildly between North and South India."
    },
    {
        "canonical": "saraswati",
        "variants": ["saraswathi", "sarasvati", "sarswati", "saraswathi"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "durga",
        "variants": ["durgaa", "doorgaa", "durga"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "parvati",
        "variants": ["parbati", "parvathi", "parbathi"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "radha",
        "variants": ["radhaa", "raadha", "radhe"],
        "religion": "Hindu",
        "region": "North India",
        "notes": ""
    },
    {
        "canonical": "narayana",
        "variants": ["narayan", "narayanan", "narayan", "narain", "nrayan"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": "South Indian form adds terminal -an."
    },
    {
        "canonical": "venkatesh",
        "variants": ["venkatesha", "venkatesh", "venkatesh", "venkates",
                     "venky", "venki"],
        "religion": "Hindu",
        "region": "South India",
        "notes": "Venky/Venki are common informal forms."
    },
    {
        "canonical": "subramaniam",
        "variants": ["subramanian", "subramanyam", "subramanyan",
                     "subramani", "subbu"],
        "religion": "Hindu",
        "region": "South India",
        "notes": ""
    },
    {
        "canonical": "murugan",
        "variants": ["murughan", "murugesan", "murgan"],
        "religion": "Hindu",
        "region": "South India (Tamil)",
        "notes": ""
    },
    {
        "canonical": "palaniswami",
        "variants": ["palaniswamy", "palanisamy", "palani"],
        "religion": "Hindu",
        "region": "South India (Tamil)",
        "notes": ""
    },
    {
        "canonical": "chandrasekhar",
        "variants": ["chandrashekhar", "chandrashekar", "chandrasekhar",
                     "chandra sekhar"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "balakrishnan",
        "variants": ["balakrishna", "balakrishnan", "bala krishnan", "bala"],
        "religion": "Hindu",
        "region": "South India",
        "notes": ""
    },
    {
        "canonical": "prasad",
        "variants": ["prashad", "prasaad", "prasath"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": "Often used as a suffix (Venkata Prasad) or standalone."
    },
    {
        "canonical": "kumar",
        "variants": ["cumar", "kumaar", "kmr"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": "Middle name/suffix; OCR sometimes drops the 'a'."
    },
    {
        "canonical": "devi",
        "variants": ["debi", "devi", "debee", "deby"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": "Female suffix; spelling varies especially in East India (Debi)."
    },
    {
        "canonical": "shankar",
        "variants": ["shanker", "shankara", "sankar", "sankara"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": "South Indian form is Sankar."
    },
    {
        "canonical": "pandey",
        "variants": ["pande", "panday", "pandi", "pandit"],
        "religion": "Hindu",
        "region": "North India",
        "notes": "Brahmin caste surname."
    },
    {
        "canonical": "sharma",
        "variants": ["sarma", "sherma", "shrama", "sarmah"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": "Sarmah form is common in Assam."
    },
    {
        "canonical": "verma",
        "variants": ["varma", "varmaa", "verma"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": "Varma form predominant in South India."
    },
    {
        "canonical": "mishra",
        "variants": ["misra", "mirshra", "mishra", "meshra"],
        "religion": "Hindu",
        "region": "North India",
        "notes": ""
    },
    {
        "canonical": "tiwari",
        "variants": ["tewari", "tivari", "tiwary", "tewary"],
        "religion": "Hindu",
        "region": "North India",
        "notes": ""
    },
    {
        "canonical": "dubey",
        "variants": ["dube", "dubey", "dubay", "dvibedi"],
        "religion": "Hindu",
        "region": "North India",
        "notes": ""
    },
    {
        "canonical": "jha",
        "variants": ["jhaa", "jaa", "ja"],
        "religion": "Hindu",
        "region": "East India (Mithila/Bihar)",
        "notes": "Maithil Brahmin surname; OCR often drops the h."
    },
    {
        "canonical": "yadav",
        "variants": ["yadaw", "yadab", "yaadav", "yadava"],
        "religion": "Hindu",
        "region": "North India",
        "notes": ""
    },
    {
        "canonical": "patel",
        "variants": ["patil", "patel", "patell", "patael"],
        "religion": "Hindu",
        "region": "West/South India",
        "notes": "Patil form dominant in Maharashtra."
    },
    {
        "canonical": "chaudhary",
        "variants": ["chaudhury", "choudhary", "choudhury", "chowdhury",
                     "chowdhary", "chodhary", "chodhari"],
        "religion": "Mixed",
        "region": "North/East India",
        "notes": "Extremely variable spelling across states."
    },
    {
        "canonical": "singh",
        "variants": ["sinha", "sing", "singg", "singhh"],
        "religion": "Mixed",
        "region": "pan-India",
        "notes": "Sinha is the Bengali/Bihari variant of Singh."
    },

    # ─────────────────────────────────────────────
    # SIKH NAMES
    # ─────────────────────────────────────────────
    {
        "canonical": "gurpreet",
        "variants": ["gurprit", "gurpreet", "gurprит", "gurpreet"],
        "religion": "Sikh",
        "region": "Punjab",
        "notes": "Gender-neutral Sikh name."
    },
    {
        "canonical": "harpreet",
        "variants": ["harprit", "harpreet"],
        "religion": "Sikh",
        "region": "Punjab",
        "notes": ""
    },
    {
        "canonical": "manjeet",
        "variants": ["manjit", "manjeet", "munjeet"],
        "religion": "Sikh",
        "region": "Punjab",
        "notes": ""
    },
    {
        "canonical": "gurjeet",
        "variants": ["gurjit", "gurjeet", "gurrjeet"],
        "religion": "Sikh",
        "region": "Punjab",
        "notes": ""
    },
    {
        "canonical": "jaswant",
        "variants": ["jasvant", "jaswant", "jaswnt"],
        "religion": "Sikh",
        "region": "Punjab",
        "notes": ""
    },
    {
        "canonical": "balwant",
        "variants": ["balvant", "balwant", "balwnt"],
        "religion": "Sikh",
        "region": "Punjab",
        "notes": ""
    },
    {
        "canonical": "kulwant",
        "variants": ["kulvant", "kulwant"],
        "religion": "Sikh",
        "region": "Punjab",
        "notes": ""
    },
    {
        "canonical": "sukhwinder",
        "variants": ["sukhvinder", "sukhwinder", "sukhwindar"],
        "religion": "Sikh",
        "region": "Punjab",
        "notes": ""
    },
    {
        "canonical": "paramjit",
        "variants": ["paramjeet", "parmjit", "parmjeet"],
        "religion": "Sikh",
        "region": "Punjab",
        "notes": ""
    },
    {
        "canonical": "kaur",
        "variants": ["kour", "kaure", "kur"],
        "religion": "Sikh",
        "region": "Punjab",
        "notes": "Mandatory female middle/last name in Sikh tradition."
    },

    # ─────────────────────────────────────────────
    # CHRISTIAN / ANGLO-INDIAN NAMES
    # ─────────────────────────────────────────────
    {
        "canonical": "joseph",
        "variants": ["jose", "josip", "joseeph", "joseff"],
        "religion": "Christian",
        "region": "South India / Goa",
        "notes": "Jose is the Goan/Malayalam short form."
    },
    {
        "canonical": "thomas",
        "variants": ["tomas", "thomes", "thomos"],
        "religion": "Christian",
        "region": "South India (Kerala)",
        "notes": ""
    },
    {
        "canonical": "george",
        "variants": ["gorge", "geoge", "giorgee"],
        "religion": "Christian",
        "region": "South India (Kerala)",
        "notes": ""
    },
    {
        "canonical": "mary",
        "variants": ["marie", "maria", "mery", "mariam"],
        "religion": "Christian",
        "region": "pan-India",
        "notes": ""
    },
    {
        "canonical": "francis",
        "variants": ["frances", "fransis", "fransys"],
        "religion": "Christian",
        "region": "Goa / South India",
        "notes": ""
    },
    {
        "canonical": "sebastian",
        "variants": ["sebastin", "sebastyan", "seby"],
        "religion": "Christian",
        "region": "South India",
        "notes": ""
    },

    # ─────────────────────────────────────────────
    # COMMON SUFFIXES / TITLES (handled as tokens)
    # ─────────────────────────────────────────────
    {
        "canonical": "lal",
        "variants": ["lall", "laal", "lal"],
        "religion": "Hindu",
        "region": "North India",
        "notes": "Common suffix meaning 'beloved'."
    },
    {
        "canonical": "das",
        "variants": ["dass", "daas", "das"],
        "religion": "Hindu",
        "region": "pan-India",
        "notes": "Suffix meaning 'servant' (of a deity)."
    },
    {
        "canonical": "bai",
        "variants": ["bhai", "bai", "baayi", "bayi"],
        "religion": "Hindu",
        "region": "West/South India",
        "notes": "Female suffix common in Rajasthani and Marathi names."
    },
    {
        "canonical": "ben",
        "variants": ["behn", "bhen", "ban"],
        "religion": "Hindu",
        "region": "Gujarat",
        "notes": "Female suffix in Gujarati names."
    },
    {
        "canonical": "bhai",
        "variants": ["bai", "bhayya", "bhaiya"],
        "religion": "Hindu",
        "region": "North/West India",
        "notes": "Male suffix/term of address in Gujarati names."
    },
    {
        "canonical": "amma",
        "variants": ["ammal", "ame", "amma"],
        "religion": "Hindu",
        "region": "South India",
        "notes": "Female suffix in Tamil/Telugu names."
    },
    {
        "canonical": "swamy",
        "variants": ["swami", "swamy", "svami", "svamy"],
        "religion": "Hindu",
        "region": "South India",
        "notes": "Suffix/title for saints or suffix in given names."
    },
]


# ─────────────────────────────────────────────────────────────
# Flat alias dict: variant → canonical
# Used by name_matcher.py (Tier-1 deterministic expansion)
# ─────────────────────────────────────────────────────────────
def build_flat_aliases() -> dict:
    out = {}
    for group in NAME_VARIANT_KB:
        canon = group["canonical"]
        for v in group["variants"]:
            key = v.strip().lower()
            if key and key != canon:
                out[key] = canon
    return out


FLAT_ALIASES: dict = build_flat_aliases()
