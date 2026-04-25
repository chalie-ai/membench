#!/usr/bin/env python3
"""
build_seeds.py

Defines all placeholder pools, family structures, and prompt templates.
Generates 150 biography variants (5 families × 30) and 300 project spec
variants (30 linked to bio characters). Outputs eval/step_1/seed_data.json.

Usage:
  python src/build_seeds.py                 # build seed_data.json
  python src/build_seeds.py --stats         # print distribution stats
"""

import argparse
import json
import random
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT_PATH = ROOT / "eval" / "step_1" / "seed_data.json"

RNG = random.Random(2026)

# ═══════════════════════════════════════════════════════════════════════════════
# BIOGRAPHY POOLS
# ═══════════════════════════════════════════════════════════════════════════════

# ── Identity & Demographics ──────────────────────────────────────────────────

FIRST_NAMES = [
    "Aaliya","Adaeze","Aiko","Alejandro","Amara","Anders","Anouk","Arjun",
    "Astrid","Beatriz","Callum","Camila","Chandra","Chioma","Dante","Dayo",
    "Elara","Emeka","Eshan","Farah","Finn","Greta","Hana","Ibrahim",
    "Ingrid","Isadora","Javier","Kaia","Kamau","Kenji","Layla","Leandro",
    "Lina","Luciano","Maeve","Malik","Maren","Matteo","Meera","Nadira",
    "Niko","Noor","Olga","Omar","Paloma","Priya","Rafik","Renzo",
    "Rosa","Saoirse","Sanjay","Selin","Sergei","Sienna","Tariq","Thiago",
    "Uma","Valentina","Viktor","Wren","Xiomara","Yael","Yuki","Zara",
    "Ayo","Bodhi","Cleo","Darian","Elif","Felix","Gia","Hugo",
    "Idris","Juno","Kian","Lev","Mila","Nia","Orin","Paz",
    "Quinn","Ravi","Sage","Tomas","Udo","Vera","Wes","Xander",
    "Yara","Zev","Amira","Bram","Cora","Devika","Elio","Freya",
    "Gael","Hessa","Ines","Jasper","Kira","Lior","Manu","Nyla",
    "Ola","Petra","Ren","Suki","Taj","Umi","Veda","Wyatt",
    "Xena","Yonas","Zia","Arun","Brigid","Cassius","Dina","Eben",
    "Fleur","Gideon","Hiro","Ilya","Joelle","Kai","Luna","Mosi",
    "Nadia","Orla","Pax","Rumi","Sol","Tala","Uri","Vivaan",
    "Wanda","Xavi","Yves","Zola","Asha","Beau","Celine","Dmitri",
    "Esme","Farid","Gemma","Haruki","Ira","Jules",
]

AGES = list(range(22, 78))

PRONOUNS = ["he/him", "she/her", "they/them"]

ORIGINS = [
    "Montevideo, Uruguay", "Tehran, Iran", "Osaka, Japan", "Nairobi, Kenya",
    "Berlin, Germany", "Tbilisi, Georgia", "rural Scotland, UK", "Hanoi, Vietnam",
    "Lagos, Nigeria", "Buenos Aires, Argentina", "Karachi, Pakistan",
    "Havana, Cuba", "Addis Ababa, Ethiopia", "Kyiv, Ukraine", "Athens, Greece",
    "Bogotá, Colombia", "Warsaw, Poland", "Cape Town, South Africa",
    "Jakarta, Indonesia", "Riyadh, Saudi Arabia", "Mumbai, India",
    "Accra, Ghana", "Santiago, Chile", "Dhaka, Bangladesh", "Lima, Peru",
    "Manila, Philippines", "Tunis, Tunisia", "Beirut, Lebanon",
    "Reykjavik, Iceland", "rural Appalachia, USA",
]

CURRENT_CITIES = [
    "Seattle, Washington", "Dublin, Ireland", "Richmond, Virginia",
    "Minneapolis, Minnesota", "Brussels, Belgium", "Perth, Australia",
    "Bozeman, Montana", "Chattanooga, Tennessee", "Zürich, Switzerland",
    "Copenhagen, Denmark", "Galway, Ireland", "Portland, Oregon",
    "Helsinki, Finland", "Vancouver, British Columbia", "Lisbon, Portugal",
    "Gothenburg, Sweden", "Austin, Texas", "Melbourne, Australia",
    "Raleigh, North Carolina", "Omaha, Nebraska", "Prague, Czech Republic",
    "Edinburgh, Scotland", "Savannah, Georgia", "Bologna, Italy",
    "Bergen, Norway",
]

NATIONALITIES = [
    "dual citizen (country of origin + current)", "naturalized citizen of current country",
    "permanent resident, not yet citizen", "citizen of birth country only",
    "triple nationality through family lineage",
]

ETHNICITIES = [
    "mixed heritage — South Asian and West African", "mixed heritage — East Asian and Scandinavian",
    "mixed heritage — Middle Eastern and Filipino", "mixed heritage — Eastern European and South Indian",
    "mixed heritage — British and Senegalese", "homogeneous heritage from birth country",
    "adopted — unknown biological heritage, culturally raised in birth city",
    "multiethnic — three or more distinct backgrounds",
]

HEIGHTS = [
    "155 cm", "158 cm", "160 cm", "163 cm", "165 cm", "168 cm", "170 cm",
    "173 cm", "175 cm", "178 cm", "180 cm", "183 cm", "185 cm", "188 cm",
    "190 cm", "193 cm",
]

BUILDS = [
    "slim and wiry", "stocky and muscular", "tall and lanky", "average build",
    "heavyset", "athletic and lean", "petite", "broad-shouldered",
    "compact and strong", "soft and round",
]

EYE_COLORS = [
    "dark brown", "light brown", "hazel", "green", "blue-grey", "amber",
    "near-black", "heterochromia — one brown, one green",
]

HAIR = [
    "close-cropped black hair", "long auburn waves", "salt-and-pepper buzz cut",
    "thick curly dark hair", "straight silver-grey to shoulders",
    "shaved head by choice", "braided locks past the shoulders",
    "thinning sandy blond", "jet-black bob with bangs",
    "natural coils kept short", "red dreadlocks to mid-back",
    "wavy chestnut pulled into a perpetual bun",
]

DISTINGUISHING_FEATURES = [
    "a thin scar across the left eyebrow from a childhood fall",
    "a port-wine birthmark on the right side of the neck",
    "a noticeable gap between the front teeth",
    "heavily tattooed forearms with botanical designs",
    "a prosthetic left hand, lost in an industrial accident",
    "a deep voice that doesn't match their small frame",
    "a permanent slight limp from a broken femur that healed wrong",
    "a constellation of freckles across the nose and cheeks",
    "burn scars on both hands from a kitchen accident",
    "an unusually crooked nose, broken twice and never set properly",
]

CLOTHING_STYLES = [
    "strictly functional — work boots, canvas pants, layered shirts",
    "vintage and eclectic — thrift store finds mixed with heirlooms",
    "minimalist and monochrome — black, grey, white only",
    "professional but soft — tailored blazers over comfortable knits",
    "outdoorsy — technical fabrics, hiking gear as daily wear",
    "colorful and bold — loud prints, statement jewelry",
    "understated luxury — quality fabrics, no logos",
    "cultural dress from heritage mixed with modern streetwear",
]

# ── Personality & Preferences ────────────────────────────────────────────────

PERSONALITY_CORES = [
    "extroverted, spontaneous, sometimes reckless",
    "introverted, methodical, deeply empathetic",
    "practical, no-nonsense, secretly sentimental",
    "anxious but high-functioning, fiercely loyal",
    "quiet observer who speaks only when it matters",
    "charismatic and warm but emotionally guarded",
    "blunt to a fault, unfiltered, deeply honest",
    "gentle and patient with a hidden stubborn streak",
    "restless and ambitious, always chasing the next goal",
    "dry-humored pessimist with a heart of gold",
]

PERSONALITY_SECONDARY = [
    "avoids conflict at all costs but holds grudges",
    "laughs loudly and cries easily — emotionally transparent",
    "deeply private, shares feelings only through actions",
    "thrives in chaos, falls apart in silence",
    "people-pleaser recovering from codependency",
    "competitive about everything, even trivial things",
    "natural caretaker who forgets to care for themselves",
    "intellectually curious to the point of obsession",
]

HUMOR_STYLES = [
    "deadpan and dry", "self-deprecating", "absurdist and surreal",
    "dad jokes delivered with full sincerity", "dark and morbid but never mean",
    "physical comedy — always tripping or spilling", "no sense of humor whatsoever",
    "witty and quick with wordplay",
]

LOVE_LANGUAGES = [
    "acts of service — shows love by fixing, building, cooking",
    "quality time — undivided attention is everything",
    "words of affirmation — needs to hear it to believe it",
    "physical touch — hugs, hand-holding, proximity",
    "gift giving — remembers every preference, gives thoughtfully",
]

FAV_COLORS = [
    "cobalt", "charcoal grey", "navy blue", "deep purple", "burgundy",
    "dusty rose", "forest green", "terracotta", "midnight blue", "sage",
    "mustard yellow", "rust", "teal", "ivory", "burnt sienna",
    "slate blue", "olive", "mauve", "copper", "pearl white",
]

FAV_BOOKS = [
    "One Hundred Years of Solitude by García Márquez",
    "The Remains of the Day by Kazuo Ishiguro",
    "Beloved by Toni Morrison",
    "The Master and Margarita by Mikhail Bulgakov",
    "Kitchen by Banana Yoshimoto",
    "Half of a Yellow Sun by Chimamanda Ngozi Adichie",
    "The Shadow of the Wind by Carlos Ruiz Zafón",
    "Kafka on the Shore by Haruki Murakami",
    "Homegoing by Yaa Gyasi",
    "Piranesi by Susanna Clarke",
    "no favorite — doesn't read for pleasure",
    "reads exclusively nonfiction, currently obsessed with behavioral economics",
]

FAV_MOVIES = [
    "Spirited Away (2001)", "The Shawshank Redemption (1994)",
    "Amélie (2001)", "City of God (2002)", "Pan's Labyrinth (2006)",
    "Parasite (2019)", "In the Mood for Love (2000)", "The Grand Budapest Hotel (2014)",
    "doesn't watch movies — prefers long-form TV", "watches only documentaries",
]

FAV_MUSIC_GENRES = [
    "West African highlife and afrobeat", "Scandinavian jazz",
    "classical piano — especially Debussy", "90s hip-hop, exclusively",
    "traditional folk music from their heritage", "indie rock and shoegaze",
    "electronic ambient — listens while working", "heavy metal — the louder the better",
    "bossa nova and MPB", "K-pop, unapologetically",
    "opera — attends live performances monthly", "listens to podcasts, not music",
]

FAV_CUISINES = [
    "Japanese — specifically ramen obsessed", "Ethiopian — injera is comfort food",
    "Mexican — authentic, not Tex-Mex", "Italian — simple, seasonal, peasant food",
    "Korean BBQ", "Middle Eastern — kebabs and mezze",
    "French bistro classics", "Thai street food", "Peruvian ceviche and seafood",
    "Indian — specifically South Indian dosas and chutneys",
]

FAV_SEASONS = ["spring — renewal energy", "summer — heat and long days", "autumn — melancholy beauty", "winter — quiet and introspection"]

COMFORT_FOODS = [
    "instant ramen with a fried egg at 2am", "their grandmother's rice pudding",
    "grilled cheese with tomato soup", "pho from a specific shop they'll drive an hour for",
    "buttered toast with marmite", "chapati with dal — childhood staple",
    "gas station hot dog — no shame", "homemade chicken soup, their own recipe",
    "chocolate chip cookies, slightly underbaked", "a specific brand of frozen pizza",
]

GO_TO_DRINKS = [
    "black coffee, no exceptions", "builder's tea with two sugars",
    "matcha latte, oat milk", "sparkling water with lemon — obsessively",
    "chai with cardamom, made from scratch", "cheap beer, nothing craft",
    "single malt scotch, neat", "fresh orange juice, hand-squeezed",
    "diet cola — 3-4 cans a day", "room temperature water only",
]

GUILTY_PLEASURES = [
    "online shopping when stressed", "rom-com movies they'd never admit to liking",
    "gas station snacks on road trips", "reality TV binges",
    "reading celebrity gossip magazines", "eating cereal for dinner",
    "karaoke alone in the car", "scrolling social media for hours",
    "buying books they'll never read", "expensive skincare routines",
]

CONTROVERSIAL_OPINIONS = [
    "believes the Oxford comma is optional and people who argue about it are insufferable",
    "thinks dogs are overrated and cats are superior in every way",
    "convinced that breakfast is a scam invented by cereal companies",
    "believes remote work is making people worse at their jobs",
    "thinks modern art is mostly a money laundering scheme",
    "argues that air conditioning is an environmental crime people treat as a right",
    "believes tipping culture should be abolished globally",
    "convinced that most self-help books do more harm than good",
    "thinks universities are obsolete for most careers",
    "believes social media should be age-restricted to 21+",
]

COMM_STYLES = [
    "prefers texting over calls, hates voicemail",
    "over-communicator — sends paragraphs, follows up frequently",
    "curt emails, no greetings or sign-offs",
    "prefers face-to-face, struggles with digital communication",
    "voice memos for everything — hates typing",
    "communicates through memes and links more than words",
    "formal and precise — writes emails like letters",
    "avoids communication until absolutely necessary",
]

CHRONOTYPES = [
    "strong morning person, up at 5am",
    "morning person but fights it",
    "no strong preference, adapts to schedule",
    "night owl, most productive after 10pm",
    "extreme night owl, rarely asleep before 2am",
]

POLITICALS = [
    "apolitical, hasn't voted in years, distrusts all parties",
    "conservative on cultural issues, liberal on economics",
    "progressive activist — attends protests, donates monthly",
    "libertarian — minimal government, maximum freedom",
    "centrist pragmatist — votes issue by issue",
    "politically engaged but deliberately non-partisan",
    "single-issue voter (environment) — everything else is noise",
    "disillusioned former party member, now politically homeless",
]

FEARS = [
    "losing their memory to dementia", "becoming financially dependent on others",
    "being forgotten after death", "open water — can't see the bottom",
    "public speaking despite being otherwise confident",
    "needles — has fainted during blood draws",
    "fire — traces back to a childhood incident",
    "being truly known and then rejected",
    "flying — hasn't been on a plane in a decade",
    "dogs — bitten badly as a child",
]

CATCHPHRASES = [
    "says 'listen' at the start of every sentence when passionate",
    "ends difficult conversations with 'it is what it is'",
    "constantly says 'to be fair' even when not being fair",
    "uses 'genuinely' before every compliment",
    "says 'I mean' as a filler so often friends count it",
    "always opens with 'so here's the thing'",
    "has no verbal tic — speaks with unusual precision",
    "mutters 'interesting' under their breath constantly",
]

NERVOUS_HABITS = [
    "cracks knuckles when anxious", "picks at cuticles until they bleed",
    "bounces right knee constantly when seated", "twirls hair around index finger",
    "hums a specific melody — doesn't realize they do it",
    "cleans obsessively when stressed", "goes completely silent and withdraws",
    "talks faster and louder when nervous",
    "chews the inside of their cheek", "reorganizes nearby objects",
]

HIDDEN_TALENTS = [
    "can solve a Rubik's cube in under 90 seconds",
    "perfect pitch — can identify any note by ear",
    "exceptional at mental arithmetic",
    "can forge any handwriting after seeing it once",
    "speaks fluent sign language, learned for a deaf friend",
    "competitive-level table tennis player",
    "can cook an impressive meal from any random fridge contents",
    "photographic memory for faces but terrible with names",
    "can fall asleep anywhere in under two minutes",
    "expert whistler — can whistle complex melodies",
]

# ── Health & Wellness ────────────────────────────────────────────────────────

MEDICAL_CONDITIONS = [
    "no conditions but strong family history of heart disease and stroke",
    "generalized anxiety disorder, on SSRIs for 3 years",
    "PTSD from a violent mugging, in EMDR therapy",
    "type 1 diabetes since age 11, insulin pump",
    "chronic migraines — 3-4 per month, triggered by stress",
    "Crohn's disease, in remission with biologic medication",
    "bipolar II disorder, well-managed with lamotrigine",
    "severe asthma — hospitalized twice in childhood",
    "pre-diabetic, managing with diet and exercise",
    "survived cardiac arrest at 52, has an implanted defibrillator",
    "rheumatoid arthritis in both hands, limits fine motor work",
    "no known conditions, hasn't seen a doctor in 5 years",
]

FOOD_ALLERGIES = [
    "severe allergy to shellfish and tree nuts, carries EpiPen",
    "lactose intolerant — strictly avoids dairy",
    "celiac disease — zero tolerance for gluten",
    "mild stone fruit allergy — itchy mouth but not dangerous",
    "no food allergies whatsoever",
    "allergic to soy — makes eating out extremely difficult",
    "red meat allergy from a lone star tick bite",
    "egg allergy — outgrew most of it but still avoids raw egg",
]

OTHER_ALLERGIES = [
    "no known allergies beyond food", "severe hay fever — miserable every spring",
    "allergic to cats — eyes swell shut", "penicillin allergy — documented since childhood",
    "latex allergy — discovered during a medical procedure",
    "dust mite allergy — runs HEPA filters in every room",
    "allergic to nickel — can't wear cheap jewelry",
    "no known allergies",
]

EXERCISE_ROUTINES = [
    "runs 5K every morning before dawn, rain or shine",
    "yoga four times a week, has a home studio",
    "powerlifts three times a week — can deadlift 2x body weight",
    "swimming laps at the community pool every other day",
    "hikes every weekend, climbs during the week",
    "no formal exercise — walks everywhere and considers that enough",
    "martial arts — has trained in judo for 12 years",
    "cycles to work (14 km each way) as primary exercise",
    "used to be very active, now sedentary and guilty about it",
    "dances — salsa twice a week and considers it a full workout",
]

SLEEP_PATTERNS = [
    "consistent 10pm-6am, almost military precision",
    "chronic insomnia — averages 4-5 hours with medication",
    "sleeps in two blocks — midnight to 3am, then 5am to 7am",
    "heavy sleeper, needs three alarms to wake up",
    "falls asleep easily but wakes at 3am with racing thoughts",
    "can nap anywhere for exactly 20 minutes, like a superpower",
    "needs white noise or rain sounds — silence keeps them awake",
    "sleeps with the TV on, partner hates it",
]

MENTAL_HEALTH = [
    "generally stable, sees a therapist once a month preventatively",
    "recovering from burnout — took 6 months off work last year",
    "manages seasonal depression with a light therapy lamp",
    "had a major depressive episode at 30, fully recovered with treatment",
    "high baseline anxiety, manages without medication through routines",
    "excellent mental health — genuinely content and self-aware",
    "undiagnosed but suspects ADHD based on lifelong patterns",
    "grief counseling after losing a parent 2 years ago",
]

DIET_TYPES = [
    "deeply traditional eater, suspicious of any fusion cuisine",
    "vegetarian for ethical reasons since age 16",
    "vegan for 5 years, very strict about it",
    "eats anything and everything — adventurous palate",
    "keto for medical reasons, not by choice",
    "pescatarian — fish and vegetables only",
    "no restrictions but cooks almost exclusively from scratch",
    "relies heavily on meal delivery services — hates cooking",
    "intermittent fasting — eats only between noon and 8pm",
    "gluten-free by necessity, not trend",
]

SUBSTANCE_USE = [
    "doesn't drink alcohol at all — never has",
    "social drinker — a glass of wine with dinner, rarely more",
    "recovering alcoholic — sober 8 years, attends meetings weekly",
    "drinks too much and knows it but hasn't addressed it",
    "occasional cannabis user, legal in their jurisdiction",
    "smokes cigarettes — has tried to quit four times",
    "former smoker — quit 10 years ago, still misses it",
    "no substances at all — not even caffeine",
]

# ── Lifestyle ────────────────────────────────────────────────────────────────

PETS = [
    "no pets, landlord doesn't allow them",
    "three chickens in the backyard",
    "a turtle won at a county fair 8 years ago",
    "a parrot that swears in Portuguese",
    "a ball python named Gerald",
    "two rescue cats named Miso and Noodle",
    "golden retriever named Copper, age 3",
    "a 14-year-old beagle mix, mostly deaf now",
    "one elderly cat named Professor",
    "a 60-liter tropical fish tank with 12 species",
    "two large dogs — a German shepherd and a mutt",
    "a hedgehog named Cactus",
    "no pets — travels too much",
    "a rabbit that free-roams the apartment",
    "foster parent for rescue dogs — currently has three",
]

VEHICLES = [
    "company truck provided by employer",
    "vintage 1972 VW Beetle, barely runs",
    "2019 BMW 3 Series, financed",
    "no car — bikes and uses public transit exclusively",
    "beat-up 2006 Toyota Corolla with 280,000 km",
    "electric vehicle — Tesla Model 3, bought used",
    "motorcycle — Kawasaki Ninja 650",
    "a van converted into a mobile workspace",
    "practical SUV for outdoor gear — Subaru Outback",
    "luxury lease — changes car every 2 years",
    "doesn't drive — relies on partner or rideshares",
    "inherited a classic car from a relative, keeps it garaged",
]

TECH_RELATIONSHIPS = [
    "technophobe — still prints emails, uses a paper calendar",
    "professional competence with tech, but analog hobbies",
    "early adopter — buys every new gadget on release day",
    "software engineer mindset — automates everything in their life",
    "deliberately minimal — flip phone, no social media",
    "comfortable but not enthusiastic — uses tech as a tool",
    "love-hate — spends hours online then does a digital detox",
    "builds their own computers and runs Linux on everything",
]

FINANCIALS = [
    "supporting extended family members, personally stretched thin",
    "paycheck to paycheck, one emergency away from crisis",
    "comfortable — six months of savings, no debt",
    "quietly wealthy — inherited money, doesn't flaunt it",
    "drowning in student debt — $87,000 remaining",
    "frugal by nature — saves 40% of income, lives simply",
    "volatile income — freelance, great months and terrible months",
    "recently declared bankruptcy, rebuilding from zero",
    "dual income household, upper middle class, mortgage nearly paid",
    "financially stable but anxious about money despite having enough",
]

LANGUAGES = [
    "English only", "English and Spanish (fluent)",
    "English, Farsi, and Turkish", "English, Swahili, and some French",
    "English and Dutch (fluent), learning Italian",
    "English, Mandarin, and Japanese", "English and Arabic (fluent)",
    "English, Portuguese, and Yoruba", "English and German (fluent)",
    "English, Hindi, and Tamil", "English and Korean (fluent)",
    "English, French, and Wolof", "English and Russian (fluent)",
    "English, Tagalog, and some Malay",
]

RELIGIONS = [
    "atheist since age 19, firm but not preachy",
    "devout Muslim, prays five times daily",
    "secular Jewish, observes major holidays for family",
    "Sikh, wears a turban, faith is central to identity",
    "was raised Jehovah's Witness, left the faith at 22",
    "Hindu by upbringing, practice has become personal and informal",
    "practicing Catholic, attends mass every Sunday",
    "Buddhist meditation practitioner, no formal affiliation",
    "spiritual but not religious — crystals, tarot, nature worship",
    "Quaker — attends meeting for worship, values silence and service",
    "agnostic — genuinely uncertain and comfortable with uncertainty",
    "devout Orthodox Christian, fasts regularly",
]

PRIZED_POSSESSIONS = [
    "a beat-up guitar they learned to play on",
    "their professional toolkit, accumulated over 20 years",
    "a handwritten letter from a deceased parent",
    "a first-edition book signed by the author at a reading",
    "a pocket watch passed down three generations",
    "their passport — symbol of freedom they didn't always have",
    "a quilted blanket made by their grandmother",
    "a set of chef's knives worth more than their car",
    "their childhood journal — 12 filled notebooks",
    "a ring from a relationship that ended but still meant everything",
]

HOUSING_TYPES = [
    "tiny studio apartment in the city center",
    "rented house with a backyard, shared with roommates",
    "owns a small bungalow, still paying the mortgage",
    "lives in a converted warehouse loft",
    "family home — inherited, too big for one person",
    "houseboat on a river, loves it but it leaks",
    "suburban townhouse in a quiet cul-de-sac",
    "lives above the shop/studio where they work",
    "high-rise apartment on the 14th floor, city views",
    "rural property — 5 acres, nearest neighbor 2 km away",
]

MORNING_ROUTINES = [
    "up at 5am, cold shower, journaling, then a run before work",
    "snoozes alarm four times, rushes out the door with coffee in hand",
    "meditates for 20 minutes, then a slow breakfast with the news",
    "walks the dog at dawn, eats breakfast standing up, leaves by 7",
    "no routine — every morning is chaos and improvisation",
    "up early for prayer, then a structured sequence that never varies",
    "wakes naturally without an alarm, reads for an hour before getting up",
    "gym at 6am, protein shake, cold and efficient about mornings",
]

WEEKEND_ACTIVITIES = [
    "farmers market Saturday morning, cooking project all afternoon",
    "complete hermit — doesn't leave the house if they can help it",
    "hiking or camping, refuses to waste a weekend indoors",
    "volunteering at local shelter or community organization",
    "works through the weekend, doesn't distinguish weekdays",
    "brunch with friends, then museum or gallery browsing",
    "DIY home improvement projects — always has one going",
    "long bike rides followed by pub lunches",
    "spends the entire weekend at their hobby, nothing else",
    "catches up on sleep and chores, too tired for anything social",
]

VACATION_STYLES = [
    "backpacker — hostels, street food, off the beaten path",
    "luxury resort, all-inclusive, does not want to think",
    "adventure travel — climbing, diving, extreme sports",
    "cultural immersion — homestays, cooking classes, local guides",
    "doesn't take vacations — hasn't had one in 4 years",
    "road trips with no fixed itinerary",
    "returns to the same place every year — a specific cottage or town",
    "volunteer tourism — combines travel with service work",
]

SOCIAL_MEDIA = [
    "no social media at all — deleted everything 3 years ago",
    "lurks on all platforms but never posts",
    "active Instagram — mostly food and travel photos",
    "Twitter/X power user — opinions about everything",
    "uses Facebook only to keep up with family abroad",
    "TikTok consumer, spends 2+ hours daily watching, never posts",
    "LinkedIn only — treats social media as strictly professional",
    "anonymous Reddit user with a very active account",
]

# ── Life Events ──────────────────────────────────────────────────────────────

LIFE_EVENTS = [
    "won a regional cooking competition with a family recipe",
    "volunteered with Doctors Without Borders for two years in their 20s",
    "built a cabin by hand over 3 summers using salvaged materials",
    "survived a house fire at age 12 that destroyed all family photos",
    "survived a category 4 hurricane that destroyed their home",
    "dropped out of college to care for a sick family member, returned 8 years later",
    "mentored a troubled teenager who later earned a college scholarship",
    "recovered from a gambling addiction that cost them their savings",
    "traveled to 30 countries before age 40",
    "published an article that went unexpectedly viral",
    "was wrongly arrested and spent 48 hours in jail before charges dropped",
    "discovered a hidden talent for public speaking at a friend's wedding toast",
    "lost everything in a flood and rebuilt from scratch",
    "ran a marathon with only 6 weeks of training on a dare",
    "adopted a child as a single parent",
    "witnessed a crime and testified in court despite threats",
    "started a small business that failed within 18 months",
    "was homeless for 4 months in their early 20s",
    "survived a serious car accident that required a year of rehabilitation",
    "emigrated alone to a country where they didn't speak the language",
    "found a long-lost sibling through a DNA testing service",
    "saved someone's life with CPR in a grocery store parking lot",
    "won a modest lottery prize ($25,000) and spent it all within a year",
    "taught themselves to play piano and now performs at local venues",
    "survived a near-drowning that left them afraid of water for a decade",
]

TURNING_POINTS = [
    "a single conversation with a stranger that changed their career path",
    "a health scare at 35 that forced a complete lifestyle overhaul",
    "reading a specific book that fundamentally shifted their worldview",
    "the death of a close friend that made them reprioritize everything",
    "getting fired from a job they loved — the humiliation became fuel",
    "a year living abroad that made them unable to return to their old life",
    "a betrayal by a business partner that destroyed their trust in people",
    "becoming a parent and realizing everything they thought mattered didn't",
]

BIGGEST_REGRETS = [
    "not being present when a parent died — was on the other side of the world",
    "ending a relationship for career reasons — still wonders what if",
    "not finishing their degree when they had the chance",
    "a harsh thing they said to a friend that ended the friendship forever",
    "selling a family property that can never be recovered",
    "not learning their heritage language while their grandparents were alive",
    "choosing financial security over passion in their career",
    "turning down a once-in-a-lifetime opportunity out of fear",
]

PROUDEST_MOMENTS = [
    "the day they became a citizen of their adopted country",
    "finishing a creative project that took 5 years of weekends",
    "the moment a mentee succeeded because of their guidance",
    "buying their first home with money they earned entirely themselves",
    "completing their degree as the first in their family",
    "a speech they gave that visibly moved the audience",
    "overcoming an addiction and reaching 5 years sober",
    "building something with their hands that people use every day",
]

RECURRING_DREAMS = [
    "a house with rooms they haven't discovered yet — always more doors",
    "teeth falling out during an important conversation",
    "flying low over a city they've never visited but somehow know",
    "being late for an exam in a school they never attended",
    "a conversation with a dead relative in their childhood kitchen",
    "drowning in calm, warm water without any panic",
    "walking through a forest that gets denser until they can't move",
    "a phone ringing that they can never find or answer",
]

# ── Education ────────────────────────────────────────────────────────────────

SCHOOL_TYPES = [
    "public school, large class sizes, underfunded but had great teachers",
    "private religious school — strict but excellent academics",
    "boarding school from age 13 — chose it themselves",
    "homeschooled by parents until age 16, then entered public school",
    "international school — changed schools 4 times following parents' work",
    "local village school with fewer than 100 students total",
    "magnet school for the arts", "military academy — hated it, learned discipline",
]

UNIVERSITIES = [
    "University of Edinburgh", "McGill University", "Universidad de Buenos Aires",
    "University of Cape Town", "Kyoto University", "Technical University of Munich",
    "Universidade de São Paulo", "Seoul National University",
    "no university — went straight into a trade apprenticeship",
    "community college, then transferred to state university",
    "Open University — studied part-time while working full-time",
    "dropped out after one year, self-taught from there",
]

DEGREES = [
    "BSc in Biology", "BA in Literature", "BEng in Mechanical Engineering",
    "BSc in Nursing", "BA in Philosophy", "BSc in Computer Science",
    "BA in Anthropology", "BFA in Fine Arts", "BSc in Environmental Science",
    "trade certification in welding", "culinary arts diploma",
    "no formal degree — certified through apprenticeship",
    "MSc in Public Health", "MA in Education",
]

ACADEMIC_ACHIEVEMENTS = [
    "graduated top 5% of class", "published undergraduate research",
    "won a national essay competition", "academic probation for a year, then recovered",
    "unremarkable grades but legendary among classmates for other reasons",
    "full scholarship — couldn't have attended otherwise",
    "thesis advisor wanted them to pursue a PhD, they refused",
    "started a student organization that still exists",
]

INFLUENTIAL_TEACHERS = [
    "a high school history teacher who made them care about the world",
    "a university professor who became a lifelong mentor and friend",
    "a workshop instructor who saw talent no one else noticed",
    "a music teacher who gave them their first instrument",
    "no standout teacher — largely self-motivated",
    "a coach who taught them more about life than sport",
    "a librarian who curated reading lists that shaped their mind",
    "a tough professor who almost failed them but earned their respect",
]

# ── Career ───────────────────────────────────────────────────────────────────

PROFESSIONS = [
    "building inspector", "pastry chef", "paramedic", "deep sea diver",
    "radio journalist", "air traffic controller", "sign language interpreter",
    "prison chaplain", "locksmith", "cartographer", "prosthetics designer",
    "shoe cobbler", "glaciologist", "blacksmith", "elevator repair technician",
    "marine biologist", "public school teacher", "forensic accountant",
    "renewable energy technician", "tattoo artist", "midwife",
    "archivist at a national museum", "urban beekeeper", "volcanologist",
    "freight train conductor", "wildlife veterinarian", "theater set designer",
    "immigration lawyer", "lighthouse keeper (automated, but on-site)",
    "underwater welder",
]

FIRST_JOBS = [
    "dishwasher at a family restaurant at age 15",
    "newspaper delivery — woke at 4am every day for 3 years",
    "retail at a clothing store in a mall, hated every minute",
    "farm hand on a relative's property during summers",
    "lifeguard at a community pool",
    "tutoring younger students in math",
    "fast food — still can't eat at that chain",
    "babysitting for the entire neighborhood",
    "construction laborer — learned to work with their hands",
    "intern at a local newspaper, unpaid",
]

CAREER_CHANGES = [
    "quit corporate job to pursue a trade — never looked back",
    "was laid off during a recession, retrained in a completely different field",
    "pivoted from academia to industry after failing to get tenure",
    "left a stable government job for a risky startup that didn't pan out",
    "moved from front-line work to management, misses the hands-on work",
    "went from creative work to technical work for financial stability",
    "took a 60% pay cut to do work that actually matters to them",
    "career change triggered by a health event that made office work impossible",
]

WORK_STYLES = [
    "hyper-organized — color-coded calendars, detailed task lists",
    "chaotic but effective — works in bursts of intense focus",
    "collaborative — can't work alone, needs people around",
    "solitary — does best work in complete isolation",
    "procrastinator who delivers brilliance at the last minute",
    "steady and methodical — same pace every day, never rushes",
    "multitasker who always has 5 projects going simultaneously",
    "deep focus — blocks entire days for single tasks, no interruptions",
]

SALARY_RANGES = [
    "$28,000 — barely above the poverty line for their area",
    "$42,000 — modest but manages",
    "$55,000 — comfortable for a single person",
    "$68,000 — solid middle class income",
    "$85,000 — doing well by most standards",
    "$110,000 — high earner, aware of privilege",
    "$145,000 — upper bracket, most goes to savings and family",
    "variable — between $20,000 and $80,000 depending on contracts",
]

WORKPLACE_ANECDOTES = [
    "once caught a critical safety violation that would have caused a disaster",
    "accidentally replied-all to a company-wide email with a personal complaint",
    "organized the first-ever union vote at their workplace",
    "mentored an intern who went on to become their boss",
    "was featured in an industry magazine for innovative work",
    "had a public disagreement with management that nearly got them fired",
    "discovered embezzlement by a colleague and had to decide whether to report it",
    "worked a 72-hour shift during an emergency that made local news",
]

PROFESSIONAL_ACHIEVEMENTS = [
    "holds a patent for a tool design used industry-wide",
    "published in a peer-reviewed journal — the paper is still cited",
    "received a regional award for excellence in their field",
    "built a program from scratch that's now used by 200+ organizations",
    "no notable achievements on paper, but deeply respected by peers",
    "saved their company $2M with a single process improvement",
    "trained over 500 people in their specialty throughout their career",
    "first person in their demographic to hold their specific position",
]

# ═══════════════════════════════════════════════════════════════════════════════
# FAMILY DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

FAMILIES = [
    {
        "surname": "Vasquez-Okafor",
        "origin": "Originally from Cartagena, Colombia; branches in Lagos, Nigeria",
        "tradition": "an annual three-day family reunion on the Colombian coast every January, running for 40+ years",
        "conflict": "a bitter inheritance dispute after the matriarch's death in 2019 that split the family into two factions",
        "heirloom": "a hand-carved wooden chess set made by the family patriarch in 1952",
        "recipe": "a closely guarded mole recipe that takes two days to prepare, passed down through the maternal line",
        "motto": "We eat together or we don't eat at all",
    },
    {
        "surname": "Lindqvist-Tanaka",
        "origin": "Originally from Gothenburg, Sweden; branches in Sapporo, Japan",
        "tradition": "a midsummer celebration blending Swedish and Japanese customs — pickled herring alongside onigiri, bonfires with paper lanterns",
        "conflict": "the eldest son's decision to sell the family's Gothenburg property to fund a business that failed, which the Japanese branch never forgave",
        "heirloom": "a collection of hand-painted ukiyo-e prints brought from Japan in 1968",
        "recipe": "a fusion dish called 'Nordic miso salmon' that the grandmother invented and everyone claims to make best",
        "motto": "Stillness is not silence",
    },
    {
        "surname": "Mahmoud-Reyes",
        "origin": "Originally from Alexandria, Egypt; branches in Cebu, Philippines",
        "tradition": "every family member writes a letter to the next generation on their 40th birthday, sealed and opened only after their death",
        "conflict": "a religious rift — the Egyptian side is Muslim, the Filipino side is Catholic, and a mixed-faith wedding in 2015 nearly tore the family apart",
        "heirloom": "a brass astrolabe from the 1800s, origin debated within the family",
        "recipe": "a spiced lamb and coconut stew that borrows from both Egyptian and Filipino cooking",
        "motto": "The door is always open but you must choose to walk through it",
    },
    {
        "surname": "Kowalski-Nair",
        "origin": "Originally from Kraków, Poland; branches in Kerala, India",
        "tradition": "a yearly 'Skills Exchange' weekend where every family member teaches something — from pierogi-making to classical Indian dance",
        "conflict": "the disappearance of a family member in 2008 — officially missing, presumed dead, but some believe they simply left and don't want to be found",
        "heirloom": "a set of hand-forged kitchen knives made by a great-uncle who was a blacksmith",
        "recipe": "a fusion pierogi filled with spiced potato and paneer that's become the family's signature dish",
        "motto": "Work with your hands and think with your heart",
    },
    {
        "surname": "Blackwood-Diallo",
        "origin": "Originally from Edinburgh, Scotland; branches in Dakar, Senegal",
        "tradition": "a storytelling night every Hogmanay (New Year's Eve) where the oldest living member tells a family story that hasn't been told before",
        "conflict": "a decades-long feud between two branches over a house in Edinburgh that both claim was promised to them",
        "heirloom": "a leather-bound journal from 1891 documenting a family member's journey from Scotland to West Africa",
        "recipe": "a Scotch egg recipe adapted with Senegalese spice blends — served at every family gathering without exception",
        "motto": "We remember so the dead are never silent",
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# PROJECT SPEC POOLS
# ═══════════════════════════════════════════════════════════════════════════════

PROJECT_TYPES = [
    "SaaS platform", "mobile application", "embedded systems firmware",
    "data pipeline and analytics platform", "e-commerce marketplace",
    "IoT device network", "machine learning model deployment",
    "internal enterprise tool", "API gateway and microservices migration",
    "real-time collaboration tool", "supply chain management system",
    "healthcare records platform", "fintech payment processing system",
    "educational LMS platform", "cybersecurity monitoring dashboard",
]

PROJECT_NAMES = [
    "Meridian", "Canopy", "Helix", "Pinnacle", "Lodestar", "Cornice",
    "Aqueduct", "Bastion", "Cairn", "Delphi", "Ember", "Forge",
    "Glacier", "Harbinger", "Ironclad", "Juniper", "Keystone", "Lattice",
    "Monolith", "Nexus", "Obelisk", "Parapet", "Quorum", "Rampart",
    "Sentinel", "Trellis", "Umbra", "Vanguard", "Wayfinder", "Zenith",
    "Archway", "Beacon", "Citadel", "Drift", "Eclipse", "Fathom",
    "Gantry", "Halcyon", "Ingot", "Jetstream",
]

INDUSTRIES = [
    "healthcare", "fintech", "agriculture technology", "logistics and shipping",
    "renewable energy", "education", "government services", "media and entertainment",
    "real estate", "cybersecurity", "food and beverage", "retail",
    "telecommunications", "automotive", "aerospace", "legal services",
]

COMPANY_NAMES = [
    "Stratos Systems", "Verdant Labs", "Iron Bay Technologies",
    "Clearpoint Digital", "Tundra Analytics", "Coral Reef Solutions",
    "Hearthstone Software", "Pivot North Engineering", "Duskfall Inc.",
    "Bridgewater Dynamics", "Oakmount Group", "Silverthread AI",
    "Ridgeline Platforms", "Deepwell Data", "Stormfront Consulting",
    "Bellweather Technologies", "Crosswind Labs", "Flintrock Engineering",
    "Nightjar Systems", "Talus Innovations",
]

PROJECT_DESCRIPTIONS = [
    "replacing a 15-year-old legacy system that the entire company depends on, with zero downtime tolerance",
    "building a greenfield product for a market the company has never operated in before",
    "an urgent regulatory compliance project with a hard legal deadline in 6 months",
    "a moonshot R&D project with uncertain ROI but strong executive sponsorship",
    "a cost-reduction initiative to consolidate 4 redundant internal tools into one",
    "a customer-facing product rebuild after catastrophic user feedback on the current version",
    "an internal productivity tool that started as a hackathon project and now has 500 daily users",
    "a strategic partnership integration that requires syncing with an external company's API on their timeline",
    "a platform modernization effort — moving from monolith to microservices over 18 months",
    "a new product vertical driven by a single enterprise client willing to pay $2M annually",
]

BUDGETS = [
    "$150,000 — shoestring, every dollar scrutinized",
    "$400,000 — modest but workable for a focused team",
    "$800,000 — comfortable for a 6-month build",
    "$1.5M — well-funded, can afford proper QA and DevOps",
    "$3M — substantial investment, high executive visibility",
    "$5M+ — flagship initiative with board-level reporting",
    "unfunded — bootstrapping with existing team capacity",
    "variable — milestone-based funding released in tranches",
]

TEAM_SIZES = [
    "solo developer", "2-person team", "small team of 4",
    "team of 6 with dedicated QA", "team of 8 across 2 time zones",
    "12-person cross-functional team", "20+ people across 3 departments",
    "distributed team of 15 across 5 countries",
]

TECH_STACKS = [
    "Python/Django, PostgreSQL, Redis, deployed on AWS ECS",
    "TypeScript/Next.js, Prisma, PostgreSQL, Vercel",
    "Go microservices, gRPC, CockroachDB, Kubernetes on GCP",
    "Rust backend, React frontend, SQLite for edge, Cloudflare Workers",
    "Java/Spring Boot, Oracle DB, on-premise data center (no cloud allowed)",
    "Ruby on Rails monolith, MySQL, Heroku — deliberately simple",
    "C#/.NET, Azure SQL, Azure Functions, full Microsoft stack",
    "Elixir/Phoenix, PostgreSQL, LiveView for real-time, Fly.io",
    "Python/FastAPI, MongoDB, Celery, Docker Compose, self-hosted",
    "mixed — inheriting 3 different stacks that need to interoperate",
]

ARCHITECTURE_PATTERNS = [
    "clean monolith with clear module boundaries",
    "microservices with event-driven communication via Kafka",
    "serverless functions with API Gateway orchestration",
    "modular monolith transitioning to microservices incrementally",
    "CQRS with event sourcing for audit-critical domains",
    "traditional three-tier (presentation, business logic, data)",
    "hexagonal architecture with ports and adapters",
    "micro-frontend architecture with independent team ownership",
]

DEPLOYMENT_METHODS = [
    "CI/CD via GitHub Actions, blue-green deployments",
    "manual deployments by a single DevOps person — bus factor of 1",
    "GitLab CI with rolling deployments to Kubernetes",
    "feature flags with LaunchDarkly, canary releases",
    "weekly release train — no exceptions, no hotfixes outside the train",
    "continuous deployment — every merged PR goes to production",
    "quarterly releases aligned with regulatory review cycles",
    "manual QA gate before every deployment, 2-day turnaround",
]

SECURITY_REQUIREMENTS = [
    "SOC 2 Type II compliance required before launch",
    "HIPAA compliant — all data encrypted at rest and in transit",
    "PCI DSS Level 1 — processing credit card data directly",
    "GDPR and CCPA compliant — data residency in EU required",
    "FedRAMP authorization required for government clients",
    "no specific compliance framework but penetration testing quarterly",
    "ISO 27001 certified environment required",
    "internal security audit only — no external compliance needed",
]

RISK_DESCRIPTIONS = [
    "key architect is leaving the company in 3 months",
    "the primary vendor dependency has announced end-of-life for their product",
    "scope creep from stakeholders who keep adding 'small' features",
    "the team has no experience with the chosen technology stack",
    "competitor is building the same product and is 2 months ahead",
    "the integration partner's API is undocumented and buggy",
    "budget may be cut by 30% in the next fiscal quarter",
    "regulatory requirements are still being finalized and may change",
    "performance requirements are 10x current system capacity with no additional infrastructure budget",
    "the project sponsor is about to rotate out of their role",
]

FEATURE_NAMES = [
    "user authentication and role-based access control",
    "real-time collaborative editing with conflict resolution",
    "automated billing and subscription management",
    "advanced search with faceted filtering and full-text indexing",
    "webhook integration framework for third-party tools",
    "offline-first mode with background sync",
    "audit trail logging with tamper-evident storage",
    "multi-tenant data isolation with shared infrastructure",
    "customizable dashboard with drag-and-drop widgets",
    "PDF/CSV report generation with scheduled delivery",
    "API rate limiting and usage analytics",
    "localization and internationalization for 12 languages",
    "two-factor authentication with hardware key support",
    "file upload with virus scanning and CDN distribution",
    "notification system — email, SMS, in-app, and push",
    "workflow automation engine with visual rule builder",
    "data import/export with format auto-detection",
    "A/B testing framework baked into the feature flag system",
    "SSO integration with SAML and OIDC providers",
    "customer-facing API with versioning and sandbox environment",
]

FEATURE_STATUSES = ["not started", "in design", "in progress", "in review", "blocked", "complete"]
FEATURE_PRIORITIES = ["critical — launch blocker", "high", "medium", "low — nice to have"]

MILESTONE_NAMES = [
    "Architecture review complete", "MVP feature-complete",
    "Internal alpha release", "External beta with 10 pilot users",
    "Security audit passed", "Performance benchmarks met",
    "Stakeholder demo and sign-off", "Production launch",
    "First paying customer onboarded", "Post-launch stability confirmed",
]

SUCCESS_METRICS = [
    "99.9% uptime in the first 90 days post-launch",
    "50% reduction in manual processing time for end users",
    "10,000 monthly active users within 6 months of launch",
    "customer NPS score above 40 within the first quarter",
    "API response time p95 under 200ms at peak load",
    "zero critical security incidents in the first year",
    "cost per transaction reduced by 35% compared to legacy system",
    "$500K in new revenue attributed to the product within 12 months",
    "80% feature adoption rate among pilot users",
    "pass external audit on first attempt",
]

CURRENT_BLOCKERS = [
    "waiting on legal review of the data processing agreement",
    "blocked by third-party API rate limits during testing",
    "key team member on medical leave for 6 weeks",
    "infrastructure provisioning delayed by cloud provider",
    "design disagreement between product and engineering leads",
    "none — project is currently unblocked",
    "dependency on another team's deliverable that is 3 weeks behind",
    "budget approval for a critical tool purchase still pending",
]

TECHNICAL_DEBT = [
    "no test coverage on the core billing module — deployed without tests under deadline pressure",
    "hardcoded configuration values scattered across 40+ files",
    "a 3,000-line 'God class' that handles authentication, logging, and email",
    "the ORM is bypassed with raw SQL in 30% of queries for performance, making migrations dangerous",
    "three different date formats used across the codebase with no normalization layer",
    "the CI pipeline takes 45 minutes because nobody has optimized or parallelized it",
    "no structured logging — debugging production issues requires reading stdout",
    "manageable — the team has been disciplined about addressing debt each sprint",
]

MEETING_NOTES_STYLES = [
    "detailed minutes with action items and owners",
    "sparse bullet points, often missing context",
    "recorded video calls that nobody rewatches",
    "no formal notes — decisions live in Slack threads",
    "a shared running document that's 200 pages long and unsearchable",
]

# ═══════════════════════════════════════════════════════════════════════════════
# ARTICLE POOLS (25 articles "written by the user")
# ═══════════════════════════════════════════════════════════════════════════════

ARTICLES = [
    {"title": "Why Small Teams Outperform Large Ones in Crisis",
     "summary": "An argument that teams of 3-5 consistently make better decisions under pressure than teams of 10+, drawing on emergency response, startup pivots, and military squad tactics. Includes specific case studies with named organizations and dollar figures."},
    {"title": "The Myth of the 10x Developer",
     "summary": "A critical examination of developer productivity myths. Argues that 'force multiplier' developers succeed because of environment, not innate ability. Cites studies, names specific companies, and proposes alternative metrics for engineering impact."},
    {"title": "Building in Public: A Post-Mortem of My Failed SaaS",
     "summary": "A brutally honest account of building and shutting down a SaaS product over 18 months. Includes monthly revenue numbers, marketing spend, churn rates, specific tooling decisions, and the exact moment the founder knew it was over."},
    {"title": "How I Migrated 2TB of Production Data with Zero Downtime",
     "summary": "A technical deep-dive into migrating from PostgreSQL to CockroachDB for a fintech platform. Covers the dual-write strategy, shadow testing, rollback procedures, and the 72-hour cutover weekend. Includes schema diagrams and query performance comparisons."},
    {"title": "The Case for Boring Technology in 2026",
     "summary": "Argues against adopting cutting-edge tech for production systems. Makes the case for PostgreSQL over NewSQL, monoliths over microservices, and server-rendered HTML over SPAs, with total cost of ownership analyses for each comparison."},
    {"title": "Remote Work Destroyed My Team's Culture (And How We Rebuilt It)",
     "summary": "Chronicles how a 12-person engineering team lost cohesion during the remote transition. Describes specific incidents, interpersonal conflicts, and the deliberate rituals they introduced to restore trust. Names the frameworks and tools used."},
    {"title": "What I Learned Interviewing 200 Senior Engineers",
     "summary": "Patterns from conducting 200 technical interviews over 3 years. Categorizes candidates into archetypes, identifies which interview signals actually predict job performance, and argues that most technical interviews are theater."},
    {"title": "Monitoring Is Not Observability: A Practitioner's Guide",
     "summary": "A detailed technical article distinguishing monitoring from observability. Covers OpenTelemetry instrumentation, trace-based testing, SLO/SLI design, and alert fatigue. Includes a reference architecture with specific tool recommendations and configurations."},
    {"title": "The Hidden Cost of Microservices Nobody Talks About",
     "summary": "A financial analysis of microservices adoption at a mid-size company. Calculates the actual infrastructure, tooling, cognitive overhead, and hiring costs. Compares against what a well-structured monolith would have cost. Includes real dollar figures."},
    {"title": "Writing Documentation That People Actually Read",
     "summary": "A guide to creating developer documentation that gets used. Covers information architecture, the Diátaxis framework, automated freshness checks, and how to measure documentation impact. Includes before/after examples from real projects."},
    {"title": "The Psychology of Code Review",
     "summary": "Explores how cognitive biases affect code review quality. Covers anchoring bias, the IKEA effect, authority bias, and social loafing in review contexts. Proposes a structured review checklist based on behavioral science research."},
    {"title": "Why I Stopped Using Kubernetes for Small Projects",
     "summary": "A practitioner's journey from Kubernetes enthusiasm to pragmatic simplicity. Compares operational costs and complexity of K8s vs. simple VPS deployments for projects under $50K ARR. Includes specific cost breakdowns and incident timelines."},
    {"title": "Debugging Production Issues at 3am: A Survival Guide",
     "summary": "A structured methodology for diagnosing production outages under pressure. Covers triage frameworks, communication templates for stakeholders, post-incident review processes, and personal stories from 15 years of on-call rotations."},
    {"title": "The Architecture of a One-Person SaaS",
     "summary": "Technical architecture decisions for a solo-founder running a $30K MRR SaaS. Covers stack choices, deployment automation, monitoring, customer support tooling, and the exact monthly cost breakdown of every service used."},
    {"title": "Technical Debt Is Not What You Think It Is",
     "summary": "Reframes technical debt using Ward Cunningham's original metaphor (which most people misunderstand). Distinguishes deliberate debt from reckless debt, proposes a debt register methodology, and argues that some debt should never be paid down."},
    {"title": "How We Reduced Our AWS Bill by 67% Without Losing Performance",
     "summary": "A step-by-step account of cloud cost optimization at a Series B startup. Covers reserved instance strategy, right-sizing, spot instances for batch jobs, data transfer optimization, and the governance process that prevented cost regression."},
    {"title": "The Unreasonable Effectiveness of Plain Text",
     "summary": "An essay arguing that plain text files (Markdown, CSV, YAML) are undervalued as a data format. Covers version control friendliness, longevity, tooling ecosystem, and specific use cases where plain text outperforms databases and SaaS tools."},
    {"title": "Leadership Lessons from Open Source Maintainers",
     "summary": "Profiles 5 open source maintainers and the management lessons embedded in how they run projects. Covers governance models, conflict resolution, contributor motivation, and burnout prevention. Each profile includes specific project names and contributor counts."},
    {"title": "The Complete Guide to Database Indexing Mistakes",
     "summary": "A comprehensive guide to indexing anti-patterns in PostgreSQL and MySQL. Covers over-indexing, composite index ordering errors, partial index opportunities, and the EXPLAIN ANALYZE output that reveals each problem. Includes benchmark numbers."},
    {"title": "Why Your Startup Doesn't Need a Data Warehouse Yet",
     "summary": "Argues that most pre-Series B startups over-invest in data infrastructure. Proposes a 'data maturity model' with specific criteria for when to adopt each layer. Includes cost comparisons between Snowflake, BigQuery, and just using PostgreSQL."},
    {"title": "Designing APIs That Don't Break: A Versioning Strategy",
     "summary": "A detailed API versioning strategy covering URL versioning, header-based versioning, and evolution without versioning. Includes specific deprecation policies, client migration tooling, and a case study of a breaking change that cost $200K in engineering time."},
    {"title": "The Art of the Blameless Post-Mortem",
     "summary": "A practical guide to conducting post-mortems that actually improve reliability. Covers facilitation techniques, the 'five whys' anti-pattern, contributing factor analysis, and how to write action items that don't rot in a backlog. Includes 3 real anonymized examples."},
    {"title": "My Unpopular Opinion: ORMs Are Mostly Fine",
     "summary": "Defends ORM usage against the 'just write SQL' crowd. Argues that for 90% of CRUD applications, ORMs reduce bugs and improve velocity. Acknowledges the 10% where they fail and provides specific guidance on when to drop to raw SQL."},
    {"title": "How I Accidentally Built a Distributed System",
     "summary": "A cautionary tale of a simple web app that grew into an unintentional distributed system. Covers the cascade of decisions — caching, job queues, separate services — that created distributed system problems without distributed system tooling."},
    {"title": "The Manager's Guide to Technical Decisions You Shouldn't Make",
     "summary": "Written for engineering managers: which technical decisions to delegate vs. own. Covers framework choices, architecture patterns, coding standards, and vendor selection. Argues that the best managers create decision-making frameworks, not decisions."},
]

ARTICLE_TEMPLATE = """Write a detailed, well-researched article titled "{title}".

The article must be approximately 5,000 words and written in first person as if by an experienced \
software engineer and technical leader sharing hard-won insights. The tone should be conversational \
but authoritative — like a long-form blog post on a personal engineering blog.

Here is the core premise and what it must cover:
{summary}

=== REQUIREMENTS ===
1. Start with a compelling personal anecdote that hooks the reader
2. Include at least 5 specific, named examples (companies, tools, projects, people)
3. Include at least 3 code snippets or configuration examples where relevant
4. Include specific numbers: dollar amounts, percentages, time durations, team sizes
5. Have clear section headers (at least 6 sections)
6. End with actionable takeaways — at least 5 specific recommendations
7. Include at least 2 counterarguments to the main thesis and address them honestly
8. Reference at least 3 specific books, papers, or talks by name and author
9. Include a personal failure story related to the topic
10. The writing should have personality — humor, strong opinions, and occasional profanity (mild)
11. Do NOT use bullet points in the main body — use flowing paragraphs with section breaks
12. Include at least one analogy or metaphor that runs through the entire piece"""

# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

BIO_TEMPLATE = """Write a detailed, comprehensive biography of a fictional person named {name}. \
The biography must be at least 5,000 words and written in third person as a factual life record — \
like a detailed case file, intake document, or investigative profile.

Use ALL of the details below as the foundation — do not change, omit, or contradict any of them. \
Expand each point with realistic, specific detail: dates, place names, amounts, measurements, anecdotes, \
and turning points. Be specific with numbers.

Do NOT use bullet points. Write in flowing prose paragraphs organized by life period and theme.

=== IDENTITY & APPEARANCE ===
- Full name: {name}
- Age: {age}
- Pronouns: {pronouns}
- Born and raised: {origin}
- Current residence: {current_city}
- Nationality: {nationality}
- Heritage: {ethnicity}
- Height: {height}
- Build: {build}
- Eyes: {eye_color}
- Hair: {hair}
- Distinguishing feature: {distinguishing_feature}
- Clothing style: {clothing_style}

=== FAMILY (THE {family_surname} CLAN) ===
- Family surname: {family_surname}
- Family roots: {family_origin}
- Family tradition: {family_tradition}
- Family conflict: {family_conflict}
- Family heirloom: {family_heirloom}
- Family recipe: {family_recipe}
- Family motto: {family_motto}
- This person's family role: {family_role}
- Inherited trait or mannerism: {inherited_trait}

=== EDUCATION ===
- School background: {school_type}
- University/Training: {university}
- Degree/Certification: {degree}
- Academic achievement: {academic_achievement}
- Influential teacher: {influential_teacher}

=== CAREER ===
- Current profession: {profession}
- First job: {first_job}
- Major career change: {career_change}
- Work style: {work_style}
- Salary: {salary_range}
- Workplace anecdote: {workplace_anecdote}
- Professional achievement: {professional_achievement}

=== PERSONALITY ===
- Core traits: {personality_core}
- Secondary traits: {personality_secondary}
- Humor style: {humor_style}
- Love language: {love_language}
- Communication style: {comm_style}
- Catchphrase/verbal tic: {catchphrase}
- Nervous habit: {nervous_habit}
- Hidden talent: {hidden_talent}

=== PREFERENCES ===
- Favorite color: {fav_color}
- Favorite book: {fav_book}
- Favorite movie: {fav_movie}
- Favorite music: {fav_music}
- Favorite cuisine: {fav_cuisine}
- Favorite season: {fav_season}
- Comfort food: {comfort_food}
- Go-to drink: {go_to_drink}
- Guilty pleasure: {guilty_pleasure}
- Controversial opinion: {controversial_opinion}

=== HEALTH & WELLNESS ===
- Medical: {medical_condition}
- Food allergy: {food_allergy}
- Other allergy: {other_allergy}
- Exercise: {exercise_routine}
- Sleep: {sleep_pattern}
- Mental health: {mental_health}
- Diet: {diet_type}
- Substance use: {substance_use}

=== LIFESTYLE ===
- Chronotype: {chronotype}
- Pet(s): {pet}
- Vehicle: {vehicle}
- Tech relationship: {tech_relationship}
- Financial situation: {financial}
- Languages: {languages}
- Religion/Spiritual: {religion}
- Prized possession: {prized_possession}
- Housing: {housing_type}
- Morning routine: {morning_routine}
- Weekend activity: {weekend_activity}
- Vacation style: {vacation_style}
- Social media: {social_media}
- Political leaning: {political}

=== LIFE EVENTS ===
- Event 1: {life_event_1}
- Event 2: {life_event_2}
- Event 3: {life_event_3}
- Event 4: {life_event_4}
- Event 5: {life_event_5}
- Turning point: {turning_point}
- Biggest regret: {biggest_regret}
- Proudest moment: {proudest_moment}
- Greatest fear: {fear}
- Recurring dream: {recurring_dream}

=== REQUIRED SECTIONS (must all appear) ===
1. Childhood & early years with at least two specific memories and named locations
2. Education history with institution names, years, and specific experiences
3. Career trajectory with at least 3 job changes, each with dates, employer names, and reasons for leaving
4. Complete medical/health history with diagnosis dates and treatment details
5. Family dynamics — detailed relationships with each family member mentioned
6. Romantic history — how they met their partner (or dating history if single), with dates and names
7. Daily routine — a typical Tuesday described hour by hour
8. Finances — specific dollar amounts, debts, savings, spending habits
9. A section on their relationship with their {family_surname} family, including specific interactions with at least two named relatives
10. Current goals, worries, and what they think about at 3am
11. At least 5 specific opinions on: a movie, a food, a city, a public figure, and a technology
12. Physical description woven throughout, not as a separate block
13. At least 3 direct quotes from this person in dialogue format"""

PROJECT_TEMPLATE = """Write a detailed project specification document for a {project_type} project \
called "{project_name}". The document must be between 6,000 and 8,000 words and written as a formal \
project specification that a development team would reference daily.

Use ALL of the details below as the foundation — do not change, omit, or contradict any of them. \
Expand each with realistic specifics: version numbers, exact dates, dollar amounts, endpoint paths, \
database schema details, and meeting notes.

=== PROJECT OVERVIEW ===
- Project name: {project_name}
- Project type: {project_type}
- Industry: {industry}
- Company: {company_name}
- Description: {project_description}
- Budget: {budget}
- Team size: {team_size}

=== TEAM ===
- Project lead: {lead_name} ({lead_role})
- Team member 1: {member_1_name} ({member_1_role})
- Team member 2: {member_2_name} ({member_2_role})
- Team member 3: {member_3_name} ({member_3_role})
- Team dynamic: {team_dynamic}

=== TECHNICAL ARCHITECTURE ===
- Stack: {tech_stack}
- Architecture: {architecture_pattern}
- Deployment: {deployment_method}
- Security: {security_requirement}

=== FEATURES (in priority order) ===
1. {feature_1} — Priority: {feature_1_priority}, Status: {feature_1_status}
2. {feature_2} — Priority: {feature_2_priority}, Status: {feature_2_status}
3. {feature_3} — Priority: {feature_3_priority}, Status: {feature_3_status}
4. {feature_4} — Priority: {feature_4_priority}, Status: {feature_4_status}
5. {feature_5} — Priority: {feature_5_priority}, Status: {feature_5_status}

=== MILESTONES ===
- Milestone 1: {milestone_1} — Target: {milestone_1_date}
- Milestone 2: {milestone_2} — Target: {milestone_2_date}
- Milestone 3: {milestone_3} — Target: {milestone_3_date}

=== RISKS & ISSUES ===
- Risk 1: {risk_1} — Mitigation: {risk_1_mitigation}
- Risk 2: {risk_2} — Mitigation: {risk_2_mitigation}
- Current blocker: {current_blocker}
- Technical debt: {technical_debt}

=== SUCCESS CRITERIA ===
- Metric 1: {success_metric_1}
- Metric 2: {success_metric_2}

=== MEETING NOTES FORMAT ===
- Style: {meeting_notes_style}

=== REQUIRED SECTIONS (must all appear) ===
1. Executive summary (500 words) with business justification and ROI projection
2. Technical architecture section with at least one ASCII diagram description
3. Detailed feature specifications for each of the 5 features (at least 400 words each)
4. API endpoint documentation for at least 8 endpoints with request/response examples
5. Database schema with at least 10 tables, their relationships, and key fields
6. Deployment and infrastructure section with environment descriptions (dev, staging, prod)
7. Testing strategy covering unit, integration, and end-to-end approaches
8. Risk register with probability/impact matrix
9. Timeline with Gantt-chart-style description of phases and dependencies
10. A section of meeting notes (at least 3 meetings) showing team discussions and decisions
11. Budget breakdown by category (personnel, infrastructure, tools, contingency)
12. At least 2 appendices with supplementary technical details"""

# ═══════════════════════════════════════════════════════════════════════════════
# GENERATION LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

def pick(pool):
    return RNG.choice(pool)

def pick_n(pool, n):
    """Pick n unique items from pool. If pool too small, allow repeats."""
    if len(pool) >= n:
        return RNG.sample(pool, n)
    return [pick(pool) for _ in range(n)]

def generate_bio_variants():
    """Generate 150 biography variants across 5 families."""
    variants = []

    # Shuffle and distribute first names: 30 per family
    names_pool = list(FIRST_NAMES)
    RNG.shuffle(names_pool)
    if len(names_pool) < 150:
        raise ValueError(f"Need 150 first names, have {len(names_pool)}")

    for fi, family in enumerate(FAMILIES):
        family_names = names_pool[fi * 30 : (fi + 1) * 30]
        full_names = [f"{fn} {family['surname']}" for fn in family_names]

        for mi in range(30):
            # Pick 2-3 relatives to reference
            rel_indices = [j for j in range(30) if j != mi]
            RNG.shuffle(rel_indices)
            ref_count = RNG.choice([2, 3])
            relatives = rel_indices[:ref_count]

            relationship_labels = ["cousin", "sibling", "uncle/aunt", "in-law", "second cousin", "niece/nephew"]
            family_role_parts = []
            for ri in relatives:
                label = pick(relationship_labels)
                family_role_parts.append(f"{label} of {full_names[ri]}")
            family_role = "; ".join(family_role_parts)

            # Pick 5 unique life events
            events = pick_n(LIFE_EVENTS, 5)

            vid = fi * 30 + mi
            variant = {
                "id": vid,
                "type": "biography",
                "family": family["surname"],
                "name": full_names[mi],
                "age": str(pick(AGES)),
                "pronouns": pick(PRONOUNS),
                "origin": pick(ORIGINS),
                "current_city": pick(CURRENT_CITIES),
                "nationality": pick(NATIONALITIES),
                "ethnicity": pick(ETHNICITIES),
                "height": pick(HEIGHTS),
                "build": pick(BUILDS),
                "eye_color": pick(EYE_COLORS),
                "hair": pick(HAIR),
                "distinguishing_feature": pick(DISTINGUISHING_FEATURES),
                "clothing_style": pick(CLOTHING_STYLES),
                "family_surname": family["surname"],
                "family_origin": family["origin"],
                "family_tradition": family["tradition"],
                "family_conflict": family["conflict"],
                "family_heirloom": family["heirloom"],
                "family_recipe": family["recipe"],
                "family_motto": family["motto"],
                "family_role": family_role,
                "inherited_trait": pick(PRIZED_POSSESSIONS),  # reuse pool as inherited item
                "school_type": pick(SCHOOL_TYPES),
                "university": pick(UNIVERSITIES),
                "degree": pick(DEGREES),
                "academic_achievement": pick(ACADEMIC_ACHIEVEMENTS),
                "influential_teacher": pick(INFLUENTIAL_TEACHERS),
                "profession": pick(PROFESSIONS),
                "first_job": pick(FIRST_JOBS),
                "career_change": pick(CAREER_CHANGES),
                "work_style": pick(WORK_STYLES),
                "salary_range": pick(SALARY_RANGES),
                "workplace_anecdote": pick(WORKPLACE_ANECDOTES),
                "professional_achievement": pick(PROFESSIONAL_ACHIEVEMENTS),
                "personality_core": pick(PERSONALITY_CORES),
                "personality_secondary": pick(PERSONALITY_SECONDARY),
                "humor_style": pick(HUMOR_STYLES),
                "love_language": pick(LOVE_LANGUAGES),
                "comm_style": pick(COMM_STYLES),
                "catchphrase": pick(CATCHPHRASES),
                "nervous_habit": pick(NERVOUS_HABITS),
                "hidden_talent": pick(HIDDEN_TALENTS),
                "fav_color": pick(FAV_COLORS),
                "fav_book": pick(FAV_BOOKS),
                "fav_movie": pick(FAV_MOVIES),
                "fav_music": pick(FAV_MUSIC_GENRES),
                "fav_cuisine": pick(FAV_CUISINES),
                "fav_season": pick(FAV_SEASONS),
                "comfort_food": pick(COMFORT_FOODS),
                "go_to_drink": pick(GO_TO_DRINKS),
                "guilty_pleasure": pick(GUILTY_PLEASURES),
                "controversial_opinion": pick(CONTROVERSIAL_OPINIONS),
                "medical_condition": pick(MEDICAL_CONDITIONS),
                "food_allergy": pick(FOOD_ALLERGIES),
                "other_allergy": pick(OTHER_ALLERGIES),
                "exercise_routine": pick(EXERCISE_ROUTINES),
                "sleep_pattern": pick(SLEEP_PATTERNS),
                "mental_health": pick(MENTAL_HEALTH),
                "diet_type": pick(DIET_TYPES),
                "substance_use": pick(SUBSTANCE_USE),
                "chronotype": pick(CHRONOTYPES),
                "pet": pick(PETS),
                "vehicle": pick(VEHICLES),
                "tech_relationship": pick(TECH_RELATIONSHIPS),
                "financial": pick(FINANCIALS),
                "languages": pick(LANGUAGES),
                "religion": pick(RELIGIONS),
                "prized_possession": pick(PRIZED_POSSESSIONS),
                "housing_type": pick(HOUSING_TYPES),
                "morning_routine": pick(MORNING_ROUTINES),
                "weekend_activity": pick(WEEKEND_ACTIVITIES),
                "vacation_style": pick(VACATION_STYLES),
                "social_media": pick(SOCIAL_MEDIA),
                "political": pick(POLITICALS),
                "life_event_1": events[0],
                "life_event_2": events[1],
                "life_event_3": events[2],
                "life_event_4": events[3],
                "life_event_5": events[4],
                "turning_point": pick(TURNING_POINTS),
                "biggest_regret": pick(BIGGEST_REGRETS),
                "proudest_moment": pick(PROUDEST_MOMENTS),
                "fear": pick(FEARS),
                "recurring_dream": pick(RECURRING_DREAMS),
            }
            variants.append(variant)

    return variants


def generate_project_variants(bio_variants):
    """Generate 300 project spec variants. 30 are linked to bio characters."""
    variants = []

    # Pick 30 bios to link — 10 from 3 different families
    families_for_linking = RNG.sample(FAMILIES, 3)
    linked_bios = []
    for fam in families_for_linking:
        fam_bios = [b for b in bio_variants if b["family"] == fam["surname"]]
        linked_bios.extend(RNG.sample(fam_bios, min(10, len(fam_bios))))

    # Group linked bios into trios (each project links to 3 people)
    RNG.shuffle(linked_bios)
    bio_trios = [linked_bios[i:i+3] for i in range(0, 30, 3)]

    for pid in range(300):
        # Pick 5 features
        features = pick_n(FEATURE_NAMES, 5)
        # Pick 3 milestones
        milestones = pick_n(MILESTONE_NAMES, 3)
        # Pick 2 risks
        risks = pick_n(RISK_DESCRIPTIONS, 2)
        # Pick 2 metrics
        metrics = pick_n(SUCCESS_METRICS, 2)

        # Team members — for linked projects, use bio character names
        is_linked = pid < 10  # first 10 projects are linked
        linked_bio_ids = None

        if is_linked and pid < len(bio_trios):
            trio = bio_trios[pid]
            linked_bio_ids = [b["id"] for b in trio]
            # Mix obvious and subtle: lead is obvious, member_3 is subtle
            lead_name = trio[0]["name"]
            lead_role = f"Project Lead — also works as {trio[0]['profession']}"
            m1_name = trio[1]["name"]
            m1_role = "Senior Developer"
            m2_name = trio[2]["name"]
            m2_role = f"Consultant (mentioned in meeting notes as external advisor from {trio[2]['current_city']})"
            m3_name = pick(FIRST_NAMES) + " " + pick([f["surname"] for f in FAMILIES])
            m3_role = "QA Engineer"
        else:
            # Generate team from name pools
            team_firsts = pick_n(FIRST_NAMES, 4)
            team_surns = ["Park", "Jensen", "Costa", "Oduya", "Kim", "Fischer",
                          "Moreau", "Gupta", "Stein", "Nakamura", "Santos", "Liu"]
            lead_name = f"{team_firsts[0]} {pick(team_surns)}"
            lead_role = pick(["Engineering Manager", "Tech Lead", "CTO", "VP of Product"])
            m1_name = f"{team_firsts[1]} {pick(team_surns)}"
            m1_role = pick(["Senior Backend Engineer", "Frontend Lead", "DevOps Engineer", "Data Engineer"])
            m2_name = f"{team_firsts[2]} {pick(team_surns)}"
            m2_role = pick(["Product Designer", "UX Researcher", "QA Lead", "Security Engineer"])
            m3_name = f"{team_firsts[3]} {pick(team_surns)}"
            m3_role = pick(["Junior Developer", "Intern", "Contractor", "Support Engineer"])

        # Milestone dates
        base_year = RNG.choice([2025, 2026])
        base_month = RNG.randint(1, 6)
        m_dates = []
        for i in range(3):
            m = base_month + (i + 1) * 2
            y = base_year + (m - 1) // 12
            m = ((m - 1) % 12) + 1
            m_dates.append(f"{y}-{m:02d}-15")

        variant = {
            "id": pid,
            "type": "project_spec",
            "linked_bio_ids": linked_bio_ids,
            "project_name": pick(PROJECT_NAMES),
            "project_type": pick(PROJECT_TYPES),
            "industry": pick(INDUSTRIES),
            "company_name": pick(COMPANY_NAMES),
            "project_description": pick(PROJECT_DESCRIPTIONS),
            "budget": pick(BUDGETS),
            "team_size": pick(TEAM_SIZES),
            "lead_name": lead_name,
            "lead_role": lead_role,
            "member_1_name": m1_name,
            "member_1_role": m1_role,
            "member_2_name": m2_name,
            "member_2_role": m2_role,
            "member_3_name": m3_name,
            "member_3_role": m3_role,
            "team_dynamic": pick(["high-trust, low-ceremony — decisions made in Slack",
                                   "formal — everything goes through JIRA and weekly status meetings",
                                   "dysfunctional — PM and lead engineer don't speak to each other",
                                   "new team, still forming — trust is being built sprint by sprint",
                                   "veteran team — worked together on 3 prior projects",
                                   "remote-first with async standups and weekly sync calls"]),
            "tech_stack": pick(TECH_STACKS),
            "architecture_pattern": pick(ARCHITECTURE_PATTERNS),
            "deployment_method": pick(DEPLOYMENT_METHODS),
            "security_requirement": pick(SECURITY_REQUIREMENTS),
            "feature_1": features[0],
            "feature_1_priority": pick(FEATURE_PRIORITIES),
            "feature_1_status": pick(FEATURE_STATUSES),
            "feature_2": features[1],
            "feature_2_priority": pick(FEATURE_PRIORITIES),
            "feature_2_status": pick(FEATURE_STATUSES),
            "feature_3": features[2],
            "feature_3_priority": pick(FEATURE_PRIORITIES),
            "feature_3_status": pick(FEATURE_STATUSES),
            "feature_4": features[3],
            "feature_4_priority": pick(FEATURE_PRIORITIES),
            "feature_4_status": pick(FEATURE_STATUSES),
            "feature_5": features[4],
            "feature_5_priority": pick(FEATURE_PRIORITIES),
            "feature_5_status": pick(FEATURE_STATUSES),
            "milestone_1": milestones[0],
            "milestone_1_date": m_dates[0],
            "milestone_2": milestones[1],
            "milestone_2_date": m_dates[1],
            "milestone_3": milestones[2],
            "milestone_3_date": m_dates[2],
            "risk_1": risks[0],
            "risk_1_mitigation": pick(["accept the risk and monitor weekly",
                                        "escalate to steering committee for additional funding",
                                        "build a contingency plan with a fallback architecture",
                                        "hire a contractor to reduce bus factor",
                                        "negotiate timeline extension with stakeholders",
                                        "parallel-path: prototype alternative approach simultaneously"]),
            "risk_2": risks[1],
            "risk_2_mitigation": pick(["document workarounds and share with the team",
                                        "assign dedicated owner to track and resolve",
                                        "raise in next board meeting as a blocker",
                                        "de-scope affected features if unresolved by milestone date",
                                        "engage external consultant for an independent assessment"]),
            "current_blocker": pick(CURRENT_BLOCKERS),
            "technical_debt": pick(TECHNICAL_DEBT),
            "success_metric_1": metrics[0],
            "success_metric_2": metrics[1],
            "meeting_notes_style": pick(MEETING_NOTES_STYLES),
        }
        variants.append(variant)

    return variants


def generate_article_variants():
    """Generate 25 article variants from the ARTICLES pool."""
    variants = []
    for aid, article in enumerate(ARTICLES):
        variants.append({
            "id": aid,
            "type": "article",
            "title": article["title"],
            "summary": article["summary"],
        })
    return variants


def print_stats(bio_variants, project_variants):
    """Print distribution stats for key fields."""
    from collections import Counter

    print(f"\n{'='*60}")
    print(f" BIOGRAPHY STATS ({len(bio_variants)} variants)")
    print(f"{'='*60}")

    for field in ["family", "current_city", "profession", "origin", "fav_color",
                   "chronotype", "religion", "pet", "age"]:
        c = Counter(v[field] for v in bio_variants)
        print(f"\n  {field} ({len(c)} distinct)")
        for val, cnt in c.most_common(3):
            print(f"    {cnt:>3}x  {val}")

    print(f"\n{'='*60}")
    print(f" PROJECT STATS ({len(project_variants)} variants)")
    print(f"{'='*60}")

    linked = sum(1 for v in project_variants if v["linked_bio_ids"])
    print(f"\n  Linked to bio characters: {linked}")

    for field in ["project_type", "industry", "tech_stack", "company_name"]:
        c = Counter(v[field] for v in project_variants)
        print(f"\n  {field} ({len(c)} distinct)")
        for val, cnt in c.most_common(3):
            print(f"    {cnt:>3}x  {val}")

    # Count total placeholder fields
    bio_fields = len([k for k in bio_variants[0] if k not in ("id", "type", "family")])
    proj_fields = len([k for k in project_variants[0] if k not in ("id", "type", "linked_bio_ids")])
    print(f"\n  Bio placeholder fields: {bio_fields}")
    print(f"  Project placeholder fields: {proj_fields}")


def main():
    parser = argparse.ArgumentParser(description="Build seed data for membench")
    parser.add_argument("--stats", action="store_true", help="Print distribution stats")
    args = parser.parse_args()

    print("Generating biography variants...")
    bio_variants = generate_bio_variants()
    print(f"  Generated {len(bio_variants)} biographies across {len(FAMILIES)} families")

    print("Generating project spec variants...")
    project_variants = generate_project_variants(bio_variants)
    print(f"  Generated {len(project_variants)} project specs ({sum(1 for v in project_variants if v['linked_bio_ids'])} linked)")

    print("Generating article variants...")
    article_variants = generate_article_variants()
    print(f"  Generated {len(article_variants)} articles")

    if args.stats:
        print_stats(bio_variants, project_variants)

    output = {
        "bio_template": BIO_TEMPLATE,
        "project_template": PROJECT_TEMPLATE,
        "article_template": ARTICLE_TEMPLATE,
        "biographies": bio_variants,
        "project_specs": project_variants,
        "articles": article_variants,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    size_mb = OUT_PATH.stat().st_size / (1024 * 1024)
    print(f"\nWrote {OUT_PATH} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
